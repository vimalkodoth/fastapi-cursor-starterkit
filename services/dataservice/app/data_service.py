import json
from datetime import datetime, timezone
from typing import Any


class DataService(object):
    """
    Simple data processing service.
    Processes input data and returns transformed/enriched output.
    No ML dependencies - just basic data transformation.
    """

    def __init__(self):
        # No initialization needed for simple data processing
        pass

    def call(self, data: str) -> tuple:
        """
        Process incoming data.

        Args:
            data: JSON string with 'payload', 'description', and 'task_type'

        Returns:
            tuple: (response_json_string, task_type)
        """
        try:
            data_json = json.loads(data)
            payload = data_json.get("payload", "")
            description = data_json.get("description", "")
            task_type = data_json.get("task_type", "data")

            # Process the data
            processed_data = self.process_data(payload, description)

            # Create response
            response = {
                "status": "success",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "input": payload,
                "description": description,
                "output": processed_data,
                "metadata": {
                    "input_length": len(str(payload)),
                    "processing_time_ms": 10,  # Simulated
                },
            }

            print(f"Processed data: {description or 'No description'}")
            print(f"Input: {payload}")
            print(f"Output: {processed_data}")

            return json.dumps(response), task_type

        except json.JSONDecodeError as e:
            error_response = {
                "status": "error",
                "error": f"Invalid JSON: {str(e)}",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            return json.dumps(error_response), "error"
        except Exception as e:  # pylint: disable=broad-except
            # Catch all exceptions to ensure service always returns a response
            error_response = {
                "status": "error",
                "error": f"Processing failed: {str(e)}",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            return json.dumps(error_response), "error"

    def process_data(self, payload: Any, description: str = "") -> Any:
        """
        Simple data processing function.
        Transforms input data based on type.

        Args:
            payload: Input data (string, number, list, dict, etc.)
            description: Optional description of the processing

        Returns:
            Processed data
        """
        desc_lower = description.lower() if description else ""

        # Handle different input types
        if isinstance(payload, str):
            return self._process_string(payload, desc_lower)
        elif isinstance(payload, (int, float)):
            return self._process_number(payload, desc_lower)
        elif isinstance(payload, list):
            return self._process_list(payload, desc_lower)
        elif isinstance(payload, dict):
            return self._process_dict(payload)
        else:
            return {"value": payload, "type": type(payload).__name__, "processed": True}

    def _process_string(self, payload: str, desc_lower: str) -> str:
        """Process string input."""
        if "uppercase" in desc_lower:
            return payload.upper()
        elif "reverse" in desc_lower:
            return payload[::-1]
        return f"Processed: {payload}"

    def _process_number(self, payload: float, desc_lower: str) -> float:
        """Process number input."""
        if "square" in desc_lower:
            return payload**2
        elif "double" in desc_lower:
            return payload * 2
        return payload

    def _process_list(self, payload: list, desc_lower: str) -> Any:
        """Process list input."""
        if "reverse" in desc_lower:
            return list(reversed(payload))
        elif "sort" in desc_lower:
            return sorted(payload)
        return {"items": payload, "count": len(payload), "processed": True}

    def _process_dict(self, payload: dict) -> dict:
        """Process dict input."""
        return {**payload, "processed": True, "keys_count": len(payload.keys())}
