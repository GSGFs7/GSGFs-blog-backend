from ninja import Router


router = Router()


# @router.get("/", response={418: None}, operation_id="root_get")
# @router.post("/", response={418: None}, operation_id="root_post")
# @router.put("/", response={418: None}, operation_id="root_put")
# @router.delete("/", response={418: None}, operation_id="root_delete")
# @router.patch("/", response={418: None}, operation_id="root_patch")
@router.api_operation(
    ["GET", "POST", "PUT", "DELETE", "PATCH"], "/", response={418: None}
)
def root_router_response(request):
    return 418, None
