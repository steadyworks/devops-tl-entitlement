# backend/route_handler/entitlement.py

from typing import Optional

from fastapi import Request
from pydantic import BaseModel

from backend.db.dal import DALEntitlements
from backend.db.dal.base import FilterOp
from backend.db.externals import EntitlementsOverviewResponse
from backend.lib.posthog import posthog_capture
from backend.route_handler.base import RouteHandler, enforce_response_model


class EntitlementStatusResponse(BaseModel):
    active: bool
    entitlement: Optional[EntitlementsOverviewResponse]


class EntitlementAPIHandler(RouteHandler):
    """
    Returns the canonical entitlement snapshot for the authenticated user.
    Web and native should reflect this value for gating (web relies on this as source of truth).
    """

    def register_routes(self) -> None:
        self.route("/api/me/entitlement", "me_entitlement", methods=["GET"])

    @enforce_response_model
    @posthog_capture()
    async def me_entitlement(self, request: Request) -> EntitlementStatusResponse:
        async with self.app.db_session_factory.new_session() as session:
            rcx = await self.get_request_context(request)

            ents = await DALEntitlements.list_all(
                session, filters={"user_id": (FilterOp.EQ, rcx.user_id)}, limit=1
            )
            ent = ents[0] if ents else None
            entitlement_resp = None
            if ent is not None:
                entitlement_resp = EntitlementsOverviewResponse.from_dao(ent)
            return EntitlementStatusResponse(
                active=ent is not None and ent.active, entitlement=entitlement_resp
            )
