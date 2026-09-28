from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("RCSBTool")
class RCSBTool(BaseTool):
    def __init__(self, tool_config):
        super().__init__(tool_config)
        # Lazy import to avoid network request during module import
        try:
            from rcsbapi.data import DataQuery

            self.DataQuery = DataQuery
        except ImportError as e:
            raise ImportError(
                "rcsbapi package is required for RCSBTool. "
                "Install it with: pip install rcsbapi"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize RCSB API client. "
                f"This may be due to network issues or API unavailability. "
                f"Original error: {str(e)}"
            ) from e

        self.name = tool_config.get("name")
        self.description = tool_config.get("description")
        self.input_type = tool_config.get("input_type")
        fields = tool_config.get("fields", {})
        self.search_fields = fields.get("search_fields", {})
        self.return_fields = fields.get("return_fields", [])
        parameter = tool_config.get("parameter", {})
        self.parameter_schema = parameter.get("properties", {})

    def validate_params(self, params: dict):
        for param_name, param_info in self.parameter_schema.items():
            if param_info.get("required", False) and param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")
        return True

    def prepare_input_ids(self, params: dict):
        for param_name in self.search_fields:
            if param_name in params:
                val = params[param_name]
                return val if isinstance(val, list) else [val]
        raise ValueError("No valid search parameter provided")

    def run(self, params: dict):
        self.validate_params(params)
        input_ids = self.prepare_input_ids(params)
        query = self.DataQuery(
            input_type=self.input_type,
            input_ids=input_ids,
            return_data_list=self.return_fields,
        )
        return query.exec()
