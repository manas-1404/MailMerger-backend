from typing import List
from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.orm import Session

from app.auth.dependency_auth import authenticate_request
from app.db.dbConnection import get_db_session
from app.db.redisConnection import get_redis_connection
from app.models.template_models import Template
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.pydantic_schemas.template_pydantic import TemplateSchema

template_router = APIRouter(
    prefix="/api/templates",
    tags=["Templates"]
)

@template_router.get("/get-all-templates")
def get_all_templates(jwt_payload: dict = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to get all templates for the authenticated user.
    """

    user_id = jwt_payload.get("sub")

    all_templates = db_connection.query(Template).filter(Template.uid == user_id).all()

    template_list = [TemplateSchema.model_validate(template).model_dump() for template in all_templates]

    return ResponseSchema(
        status_code=200,
        success=True,
        message="Templates retrieved successfully." if template_list else "No templates found for the user.",
        data={"templates": template_list}
    )


@template_router.post("/add-template")
def add_template(template_data: TemplateSchema, jwt_payload: dict = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to add a new template for the authenticated user.
    """
    user_id = jwt_payload.get("sub")

    new_template = Template(
        uid=user_id,
        t_body=template_data.t_body,
        t_key=template_data.t_key
    )

    db_connection.add(new_template)
    db_connection.commit()

    return ResponseSchema(
        status_code=201,
        success=True,
        message="Template added successfully.",
        data={"template_id": new_template.template_id}
    )

@template_router.patch("/update-template")
def update_template(template_data: TemplateSchema, jwt_payload: dict = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to update a template for the authenticated user.
    """
    user_id = jwt_payload.get("sub")

    update_template = db_connection.query(Template).filter(Template.template_id == template_data.template_id,
                                                           Template.uid == user_id).first()

    if not update_template:
        return ResponseSchema(
            success=False,
            status_code=404,
            message=f"Template with ID {template_data.template_id} not found.",
            data={}
        )

    update_template.t_body = template_data.t_body
    update_template.t_key = template_data.t_key

    db_connection.commit()

    return ResponseSchema(
        status_code=200,
        success=True,
        message="Template updated successfully.",
        data={"template_id": update_template.template_id}
    )

@template_router.delete("/delete-template")
def delete_template(template_ids: List[int] = Body(...), jwt_payload: dict = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to delete a template for the authenticated user.
    """
    user_id = jwt_payload.get("sub")

    for template_id in template_ids:

        template = db_connection.query(Template).filter(Template.template_id == template_id, Template.uid == user_id).first()

        if not template:
            return ResponseSchema(
                success=False,
                status_code=404,
                message=f"Template with ID {template_id} not found.",
                data={
                    "missing_template": template_id
                }
            )

        db_connection.delete(template)

    db_connection.commit()

    return ResponseSchema(
        status_code=200,
        success=True,
        message="Template deleted successfully.",
        data={
            "template_ids": template_ids
        }
    )