import pytest

from codemind_github_client.mock_write_client import MockGitHubWriteClient


@pytest.fixture
def client() -> MockGitHubWriteClient:
    return MockGitHubWriteClient(
        seed_files={("acme", "widgets", "src/utils/math.ts"): "export function divide(a, b) {\n  return a / b;\n}\n"}
    )


async def test_get_file_returns_seeded_content_and_sha(client: MockGitHubWriteClient):
    file = await client.get_file(owner="acme", repo="widgets", path="src/utils/math.ts", branch="main")
    assert file.path == "src/utils/math.ts"
    assert "return a / b" in file.content
    assert file.sha


async def test_get_file_raises_for_unknown_path(client: MockGitHubWriteClient):
    with pytest.raises(FileNotFoundError):
        await client.get_file(owner="acme", repo="widgets", path="src/missing.ts", branch="main")


async def test_create_branch_records_the_branch(client: MockGitHubWriteClient):
    await client.create_branch(owner="acme", repo="widgets", base_branch="main", new_branch="fix/divide")
    assert client.created_branches == [
        {"owner": "acme", "repo": "widgets", "base_branch": "main", "new_branch": "fix/divide"}
    ]


async def test_update_file_with_correct_sha_bumps_content_and_sha(client: MockGitHubWriteClient):
    original = await client.get_file(owner="acme", repo="widgets", path="src/utils/math.ts", branch="main")
    new_content = "export function divide(a, b) {\n  if (b === 0) return 0;\n  return a / b;\n}\n"

    await client.update_file(
        owner="acme",
        repo="widgets",
        path="src/utils/math.ts",
        branch="main",
        content=new_content,
        sha=original.sha,
        message="fix: guard divide by zero",
    )

    updated = await client.get_file(owner="acme", repo="widgets", path="src/utils/math.ts", branch="main")
    assert updated.content == new_content
    assert updated.sha != original.sha


async def test_update_file_with_none_sha_creates_a_new_file(client: MockGitHubWriteClient):
    await client.update_file(
        owner="acme",
        repo="widgets",
        path="src/utils/math.test.ts",
        branch="fix/divide",
        content="test('divides', () => {});\n",
        sha=None,
        message="test: add divide test",
    )
    created = await client.get_file(
        owner="acme", repo="widgets", path="src/utils/math.test.ts", branch="fix/divide"
    )
    assert created.content == "test('divides', () => {});\n"


async def test_update_file_with_none_sha_on_existing_file_raises(client: MockGitHubWriteClient):
    with pytest.raises(ValueError):
        await client.update_file(
            owner="acme",
            repo="widgets",
            path="src/utils/math.ts",
            branch="main",
            content="anything",
            sha=None,
            message="should fail — file already exists",
        )


async def test_update_file_with_stale_sha_raises(client: MockGitHubWriteClient):
    with pytest.raises(ValueError):
        await client.update_file(
            owner="acme",
            repo="widgets",
            path="src/utils/math.ts",
            branch="main",
            content="anything",
            sha="stale-sha-value",
            message="should fail",
        )


async def test_create_pull_request_records_and_returns_incrementing_numbers(client: MockGitHubWriteClient):
    pr1 = await client.create_pull_request(
        owner="acme",
        repo="widgets",
        head_branch="fix/divide",
        base_branch="main",
        title="Fix divide-by-zero",
        body="Adds a zero guard.",
    )
    pr2 = await client.create_pull_request(
        owner="acme",
        repo="widgets",
        head_branch="fix/other",
        base_branch="main",
        title="Another fix",
        body="Body",
    )

    assert pr1.number == 1
    assert pr2.number == 2
    assert pr1.url == "https://github.com/acme/widgets/pull/1"
    assert pr1.branch_name == "fix/divide"
    assert client.created_pull_requests == [pr1, pr2]
