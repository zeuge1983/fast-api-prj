"""Ask the locally running Meta Muse Glimmer model (LM Studio) to write
an automated pytest suite for the /tickets/{ticket_id} test cases."""

from pathlib import Path

from openai import OpenAI

def main() -> None:

    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
    )

    OUT_FILE = Path(__file__).parent.parent / "tests" / "test_tickets_generated.py"

    PROMPT = """
    You are a senior QA automation engineer.

    A FastAPI service is ALREADY RUNNING locally at http://127.0.0.1:8000

    Endpoint under test:  GET /tickets/{ticket_id}

    Facts about the running service (discovered from the code):
    - The path parameter is declared as `ticket_id: int`.
    - Existing ticket ids in the test data are 1001..1010.
    - A successful response body looks like:
    {"ticket_id":1001,"title":"Cannot log in","priority":"High",
    "category":"Login","status":"Open","description":"..."}
    - There is currently NO authentication on the endpoint.

    Write ONE runnable pytest module that tests the endpoint over real HTTP
    (use the `requests` library, BASE_URL = "http://127.0.0.1:8000") for the
    test cases in the table below.

    | TC-F01 | Functional | Valid ticket retrieval | Ticket 123 exists, user authorized | GET /tickets/123 + valid token | 200 OK, body contains id=123, status, priority, customer with id/name/email. Content-Type application/json |
    | TC-F02 | Functional | Response schema | - | GET /tickets/123 | All 4 fields present, types correct: id int, status string, priority string, customer object |
    | TC-N01 | Negative | Ticket not found | Ticket 999999 does not exist | GET /tickets/999999 | 404 Not Found, body { "detail": "Ticket not found" } |
    | TC-N02 | Negative | Invalid format - non numeric | - | GET /tickets/abc | 400 Bad Request, validation error |
    | TC-N03 | Negative | Invalid format - special chars | - | GET /tickets/123;DROP | 400 Bad Request, no injection execution |
    | TC-N04 | Negative | Missing auth | - | GET /tickets/123 no header | 401 Unauthorized |
    | TC-N05 | Negative | Forbidden - wrong tenant/user | Ticket belongs to user B | GET /tickets/123 as user A | 403 Forbidden |
    | TC-B01 | Boundary | Minimum valid ID | Ticket 1 exists | GET /tickets/1 | 200 OK |
    | TC-B02 | Boundary | Max int ID | Ticket at max int exists | GET /tickets/2147483647 | 200 OK or 404 if not exist, no overflow |
    | TC-B03 | Boundary | Negative ID | - | GET /tickets/-5 | 400 Bad Request |
    | TC-B04 | Boundary | Zero ID | - | GET /tickets/0 | 400 or 404, consistent |
    | TC-B05 | Boundary | UUID format if applicable | ticket_id is UUID | GET /tickets/00000000-0000-0000-0000-000000000000 | 400 if malformed UUID, 404 if well-formed but not found |

    Hard rules:
    1. Output ONLY the Python source of the test module. No markdown fences,
    no prose, no explanation before or after the code.
    2. One test function per test case, named test_tc_f01_..., test_tc_n01_...
    etc, so the TC id is visible in the pytest report.
    3. Assert the EXPECTED RESULT from the table exactly as written. Do NOT
    soften an assertion or skip a test to make it pass. A test that fails
    against the running service is a valid finding, and the point of this
    suite is to reveal such gaps.
    4. Where the table allows several outcomes ("200 OK or 404", "400 or 404"),
    assert that the status code is in the allowed set.
    5. Every test must include a clear assertion message naming the TC id.
    6. Add a module docstring, and a short comment above each test with the
    TC id and its intent.
    """

    response = client.chat.completions.create(
        model="meta/muse-glimmer",
        messages=[{"role": "user", "content": PROMPT}],
    )

    content = response.choices[0].message.content or ""

    # The model may still wrap the code in markdown fences - strip them.
    code = content.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]                      # drop opening fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]                 # drop closing fence
        code = "\n".join(lines)

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(code.rstrip() + "\n")

    print(f"Wrote {OUT_FILE} ({len(code.splitlines())} lines)")


if __name__ == "__main__":
    main()