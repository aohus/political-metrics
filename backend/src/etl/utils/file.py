import aiofiles
import json
from pathlib import Path


async def read_file(filepath: str) -> dict:
    file_path_obj = Path(filepath)
    if not file_path_obj.is_file():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
        if not content:
            return {}
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 디코딩 오류: {e} - 파일: {filepath}") from e
    return data


async def write_file(filepath: str, data) -> None:
    file_path_obj = Path(filepath)
    file_path_obj.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))
