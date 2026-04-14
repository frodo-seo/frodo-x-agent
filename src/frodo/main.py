import argparse

from .config import Config
from .llm import LLMClient
from .models import PostResult
from . import post_log
from .pipeline import draft_brief, draft_one
from .search import NagneSearch
from .validators import x_weighted_length
from .x_client import XClient


def _print_result(result: PostResult) -> None:
    print(f"\n--- Nagne draft: {result.topic} ---")
    if result.brief:
        print(f"  [brief] {result.brief.headline}  (angle: {result.brief.angle_strength})")
    if not result.text:
        print("  (no draft produced)")
    else:
        print(result.text)
        print(
            f"  ({len(result.text)} chars / {x_weighted_length(result.text)} weighted, "
            f"{result.revisions} revision(s))"
        )
    if result.final_issues:
        print("  ⚠ remaining issues:")
        for issue in result.final_issues:
            print(f"    - {issue}")


def _save_and_post(result: PostResult, cfg: Config, do_post: bool) -> None:
    if result.final_issues or not result.text or not result.brief:
        if do_post:
            print("  → skipped (issues remain)")
        return

    if not do_post:
        post_log.save(result.topic, result.brief.headline, result.text, posted=False)
        return

    if not cfg.can_post_to_x():
        raise RuntimeError(
            "Posting requires X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET."
        )
    x = XClient(
        cfg.x_api_key,  # type: ignore[arg-type]
        cfg.x_api_secret,  # type: ignore[arg-type]
        cfg.x_access_token,  # type: ignore[arg-type]
        cfg.x_access_token_secret,  # type: ignore[arg-type]
    )
    tweet_id = x.post(result.text)
    post_log.save(result.topic, result.brief.headline, result.text, posted=True)
    print(f"  → posted: https://x.com/i/web/status/{tweet_id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Nagne — daily US news, curated for Korean readers."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    draft_cmd = sub.add_parser("draft", help="Draft one post on a specific topic.")
    draft_cmd.add_argument("topic", help="Topic or headline to write about.")
    draft_cmd.add_argument("--post", action="store_true", help="Publish to X.")
    draft_cmd.add_argument("--force", action="store_true", help="Ignore dedup check.")

    brief_cmd = sub.add_parser(
        "brief", help="Auto-discover today's top stories and draft each."
    )
    brief_cmd.add_argument(
        "-n", type=int, default=1, help="How many stories to brief (default 1)."
    )
    brief_cmd.add_argument("--post", action="store_true", help="Publish to X.")

    args = parser.parse_args()

    cfg = Config.from_env()
    search = NagneSearch(cfg.tavily_api_key)
    llm = LLMClient(cfg.anthropic_api_key, cfg.model_id)

    if args.command == "draft":
        covered = post_log.recent_topics()
        topic_lower = args.topic.lower()
        duplicate = any(topic_lower in c.lower() or c.lower() in topic_lower for c in covered)
        if duplicate and not args.force:
            print(f"  [skip] '{args.topic}'은 최근 다룬 토픽과 유사 (dedup). --force로 무시 가능.")
            return
        result = draft_one(args.topic, search, llm)
        _print_result(result)
        _save_and_post(result, cfg, args.post)

    elif args.command == "brief":
        results = draft_brief(search, llm, n=args.n)
        if not results:
            print("No stories selected. Try again later.")
            return
        for result in results:
            _print_result(result)
            _save_and_post(result, cfg, args.post)

    if not args.post:
        print("\n(Dry run. Pass --post to publish.)")


if __name__ == "__main__":
    main()
