import json
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8000"


def run_case(name: str, payload: dict) -> None:
    response = requests.post(
        f"{BASE_URL}/api/vendor-quotations-bulk",
        json=payload,
        timeout=20,
    )
    print(f"[{response.status_code}] {name}")
    print(response.text[:1200])
    print("---")


if __name__ == "__main__":
    cases = [
        (
            "normal_office_request",
            {
                "item_json_string": json.dumps(
                    [
                        {
                            "name": "Dell Monitor",
                            "quantity": 2,
                            "unit": "pcs",
                            "target_unit_price": 2800,
                        },
                        {
                            "name": "Wireless Mouse",
                            "quantity": 2,
                            "unit": "pcs",
                            "target_unit_price": 299,
                        },
                    ],
                    ensure_ascii=False,
                ),
                "total_budget_mentioned": 8000,
            },
        ),
        (
            "razer_gaming_setup",
            {
                "item_json_string": json.dumps(
                    [
                        {
                            "name": "Razer BlackWidow V4 Keyboard",
                            "quantity": 2,
                            "unit": "pcs",
                            "target_unit_price": 1299,
                        },
                        {
                            "name": "Razer DeathAdder V3 Mouse",
                            "quantity": 2,
                            "unit": "pcs",
                            "target_unit_price": 499,
                        },
                        {
                            "name": "Razer Headset",
                            "quantity": 1,
                            "unit": "pcs",
                            "target_unit_price": 899,
                        },
                    ],
                    ensure_ascii=False,
                ),
                "total_budget_mentioned": 4500,
            },
        ),
        (
            "quoted_string_payload",
            {
                "item_json_string": "'[{\"name\":\"Laptop\",\"quantity\":1,\"unit\":\"pcs\",\"target_unit_price\":6000}]'",
                "total_budget_mentioned": 7000,
            },
        ),
    ]

    for case_name, case_payload in cases:
        run_case(case_name, case_payload)
