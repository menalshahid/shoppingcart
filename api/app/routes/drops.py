from uuid import UUID
import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException
from ..config import settings
from ..db import get_pool

router = APIRouter()

def current_user(x_user_id: str = Header(...)) -> str:
    # Simple identity for the assignment; document this in the README.
    return x_user_id

@router.post("/drops/{drop_id}/reserve", status_code=201)
async def reserve(
    drop_id: UUID,
    user_id: str = Depends(current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, str]:
    async with pool.acquire() as conn:
        # Raising inside this block rolls the whole transaction back,
        # which also undoes the stock decrement.
        async with conn.transaction():
            # Atomic decrement: Postgres row-locks the drop row, so
            # concurrent requests are serialized here. No overselling.
            updated = await conn.fetchrow(
                """UPDATE drops
                   SET available_stock = available_stock - 1
                   WHERE id = $1 AND available_stock > 0 AND starts_at <= now()
                   RETURNING id""",
                drop_id,
            )
            if updated is None:
                drop = await conn.fetchrow(
                    "SELECT starts_at > now() AS not_started FROM drops WHERE id = $1",
                    drop_id,
                )
                if drop is None:
                    raise HTTPException(404, {"code": "DROP_NOT_FOUND"})
                if drop["not_started"]:
                    raise HTTPException(403, {"code": "DROP_NOT_STARTED"})
                raise HTTPException(409, {"code": "SOLD_OUT"})

            try:
                res = await conn.fetchrow(
                    """INSERT INTO reservations (drop_id, user_id, expires_at)
                       VALUES ($1, $2, now() + make_interval(mins => $3))
                       RETURNING id, expires_at""",
                    drop_id, user_id, settings.reservation_ttl_minutes,
                )
            except asyncpg.UniqueViolationError:
                raise HTTPException(409, {"code": "ALREADY_RESERVED"})

            order = await conn.fetchrow(
                "INSERT INTO orders (reservation_id) VALUES ($1) RETURNING id",
                res["id"],
            )
            await conn.execute(
                """INSERT INTO order_transitions (order_id, from_status, to_status, source)
                   VALUES ($1, NULL, 'reserved', 'user')""",
                order["id"],
            )

    return {
        "reservation_id": str(res["id"]),
        "order_id": str(order["id"]),
        "expires_at": res["expires_at"].isoformat(),
    }