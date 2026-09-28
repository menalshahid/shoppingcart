from dotenv import load_dotenv
load_dotenv()
import asyncio, os
import asyncpg

async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    row = await conn.fetchrow(
        """INSERT INTO drops (name, total_stock, available_stock, starts_at)
           VALUES ('Test Drop', 100, 100, now()) RETURNING id"""
    )
    print("drop id:", row["id"])
    await conn.close()

asyncio.run(main())