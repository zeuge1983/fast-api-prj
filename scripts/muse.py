from openai import OpenAI

def main():

    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"
    )

    response = client.chat.completions.create(
        model="meta/muse-glimmer",
        messages=[
            {
                "role": "user",
                "content":"""
                    You are a senior QA engineer.

                    I have a FastAPI endpoint:

                    GET /tickets/{ticket_id}

                    It returns a ticket with:
                    - id
                    - status
                    - priority
                    - customer

                    Design a comprehensive API test strategy for this endpoint.
                    Think about functional, negative, boundary, security and data
                    validation cases.

                    Give me the answer as a structured test plan."""
            }
        ]
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()