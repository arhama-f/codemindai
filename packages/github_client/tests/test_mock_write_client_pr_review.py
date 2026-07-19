import pytest

from codemind_github_client.mock_write_client import MockGitHubWriteClient
from codemind_shared_types.schemas import PullRequestFileDTO, ReviewCommentDTO


@pytest.fixture
def client() -> MockGitHubWriteClient:
    client = MockGitHubWriteClient()
    client.seed_pull_request(
        owner="acme",
        repo="widgets",
        pr_number=7,
        head_sha="abc123",
        head_ref="fix/divide",
        base_ref="main",
        files=[
            PullRequestFileDTO(
                path="src/utils/math.ts",
                status="modified",
                patch="@@ -1,3 +1,4 @@\n context\n+  return a / b;\n context",
            )
        ],
    )
    return client


async def test_get_pull_request_returns_seeded_detail(client: MockGitHubWriteClient):
    pr = await client.get_pull_request(owner="acme", repo="widgets", pr_number=7)
    assert pr.number == 7
    assert pr.head_sha == "abc123"
    assert pr.head_ref == "fix/divide"
    assert pr.base_ref == "main"


async def test_get_pull_request_raises_for_unseeded_pr(client: MockGitHubWriteClient):
    with pytest.raises(FileNotFoundError):
        await client.get_pull_request(owner="acme", repo="widgets", pr_number=999)


async def test_get_pull_request_files_returns_seeded_files(client: MockGitHubWriteClient):
    files = await client.get_pull_request_files(owner="acme", repo="widgets", pr_number=7)
    assert len(files) == 1
    assert files[0].path == "src/utils/math.ts"
    assert files[0].status == "modified"
    assert "+  return a / b;" in files[0].patch


async def test_create_review_records_and_returns_result(client: MockGitHubWriteClient):
    result = await client.create_review(
        owner="acme",
        repo="widgets",
        pr_number=7,
        commit_sha="abc123",
        body="CodeMind found 1 issue.",
        comments=[ReviewCommentDTO(path="src/utils/math.ts", line=2, body="unsafe division")],
    )
    assert result.id == 1
    assert "pullrequestreview-1" in result.html_url
    assert len(client.created_reviews) == 1
    assert client.created_reviews[0]["pr_number"] == 7
    assert len(client.created_reviews[0]["comments"]) == 1


async def test_create_commit_status_records_the_call(client: MockGitHubWriteClient):
    await client.create_commit_status(
        owner="acme",
        repo="widgets",
        sha="abc123",
        state="failure",
        description="1 issue found",
        context="codemind-ai/pr-review",
    )
    assert client.created_commit_statuses == [
        {
            "owner": "acme",
            "repo": "widgets",
            "sha": "abc123",
            "state": "failure",
            "description": "1 issue found",
            "context": "codemind-ai/pr-review",
        }
    ]
