
from pipeline.run_agent_process import run_pipeline
import json


if __name__ == "__main__":
    # Run the main pipeline
    result = run_pipeline()
    print(json.dumps(result, indent=2, default=str))