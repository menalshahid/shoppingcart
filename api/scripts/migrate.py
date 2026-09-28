from dotenv import load_dotenv
load_dotenv()
import asyncio, os, pathlib
import asyncpg

async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)"
    )
    done = {r["name"] for r in await conn.fetch("SELECT name FROM schema_migrations")}
    for f in sorted(pathlib.Path("migrations").glob("*.sql")):
        if f.name in done:
            continue
        async with conn.transaction():
            await conn.execute(f.read_text())
            await conn.execute("INSERT INTO schema_migrations VALUES ($1)", f.name)
        print("applied", f.name)
    await conn.close()

asyncio.run(main())