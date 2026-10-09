import os
import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def normalize_key(key: str) -> str:
    k = key.strip()
    if k.upper().startswith("APP_"):
        k = k[4:]
    k_lower = k.lower()

    if k_lower in ("workers", "num_workers"):
        return "workers"
    if k_lower in ("port", "debug", "log_level", "api_key"):
        return k_lower

    return k_lower


def coerce_value(key: str, value):
    if value is None:
        return None

    if key in ("port", "workers"):
        return int(value)
    elif key == "debug":
        if isinstance(value, bool):
            return value
        val_str = str(value).strip().lower()
        return val_str in ("true", "1", "yes", "on")
    else:
        return str(value)


@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    merged = DEFAULTS.copy()

    yaml_path = "config.development.yaml"
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f) or {}
            for k, v in yaml_data.items():
                if v is not None:
                    norm_k = normalize_key(k)
                    merged[norm_k] = coerce_value(norm_k, v)

    env_path = ".env"
    if os.path.exists(env_path):
        env_data = dotenv_values(env_path)
        for k, v in env_data.items():
            if v is not None:
                norm_k = normalize_key(k)
                merged[norm_k] = coerce_value(norm_k, v)

    for k, v in os.environ.items():
        if k.startswith("APP_") or k.upper() in (
            "NUM_WORKERS",
            "PORT",
            "WORKERS",
            "DEBUG",
            "LOG_LEVEL",
            "API_KEY",
        ):
            norm_k = normalize_key(k)
            merged[norm_k] = coerce_value(norm_k, v)

    for param in set:
        if "=" in param:
            k, v = param.split("=", 1)
            norm_k = normalize_key(k)
            merged[norm_k] = coerce_value(norm_k, v)

    return {
        "port": merged.get("port"),
        "workers": merged.get("workers"),
        "debug": merged.get("debug"),
        "log_level": merged.get("log_level"),
        "api_key": "****",
    }
