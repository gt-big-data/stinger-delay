from Config import Config
from ForwardPipeline import ForwardPipeline  # wherever your class lives
from dotenv import load_dotenv

if __name__ == "__main__":
    cfg = Config()          # or Config.from_env(), Config.load(), etc.
    pipeline = ForwardPipeline(cfg)

    # run once, no DB writes, just prints
    pipeline.run_once()
