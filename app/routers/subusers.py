from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import models, schemas, auth, security_utils
from app.database import get_db

router = APIRouter(
    prefix="/subusers",
    tags=["subusers"],
)

@router.post("/", response_model=schemas.SubUserResponse)
def create_subuser(
    subuser: schemas.SubUserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Create sub-user attached to current user
    db_subuser = models.SubUser(
        name=subuser.name,
        parent_user_id=current_user.id,
        is_active=True,
        # Starts with no access (or read-only? Implementing strict no access for now until licensed)
    )
    db.add(db_subuser)
    db.commit()
    db.refresh(db_subuser)
    return db_subuser

@router.get("/", response_model=list[schemas.SubUserResponse])
def read_subusers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return current_user.subusers

@router.post("/{subuser_id}/license")
def activate_license(
    subuser_id: int,
    license_req: schemas.LicenseActivate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Verify subuser belongs to current user
    subuser = db.query(models.SubUser).filter(
        models.SubUser.id == subuser_id,
        models.SubUser.parent_user_id == current_user.id
    ).first()
    
    if not subuser:
        raise HTTPException(status_code=404, detail="Sub-user not found")
        
    # Verify License
    license_entry = db.query(models.License).filter(
        models.License.key == license_req.license_key
    ).first()
    
    if not license_entry:
        raise HTTPException(status_code=404, detail="Invalid license key")
        
    if license_entry.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="License already used or revoked")
        
    # Activate License
    license_entry.status = "USED"
    license_entry.used_by_subuser_id = subuser.id
    license_entry.activated_at = datetime.utcnow()
    
    # Extend Access
    now = datetime.utcnow()
    current_expiry = subuser.access_expires_at if subuser.access_expires_at else now
    if current_expiry < now:
        current_expiry = now
        
    subuser.access_expires_at = current_expiry + timedelta(days=license_entry.duration_days)
    
    # Generate Login Code
    raw_code = security_utils.generate_login_code()
    subuser.login_code_hash = security_utils.hash_code(raw_code)
    subuser.login_code_index = security_utils.get_code_index(raw_code)
    subuser.login_code_display = raw_code # Store for display
    
    db.commit()
    
    return {
        "message": "License activated successfully",
        "new_expiration": subuser.access_expires_at,
        "login_code": raw_code  # IMPORTANT: Display this to the user only once!
    }

@router.delete("/{subuser_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subuser(
    subuser_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    subuser = db.query(models.SubUser).filter(
        models.SubUser.id == subuser_id,
        models.SubUser.parent_user_id == current_user.id
    ).first()
    
    if not subuser:
        raise HTTPException(status_code=404, detail="Alumno/a no encontrado/a")
        
    # Handle associated licenses (Detach them, maybe keep status as USED or set to REVOKED)
    # For now, let's keep them as USED but detach to allow deletion
    licenses = db.query(models.License).filter(models.License.used_by_subuser_id == subuser.id).all()
    for lic in licenses:
        lic.used_by_subuser_id = None
        # lic.status = "REVOKED" # Optional: could revoke, or leave as USED to prevent reuse
        
    db.delete(subuser)
    db.commit()
    return None

@router.put("/{subuser_id}", response_model=schemas.SubUserResponse)
def update_subuser(
    subuser_id: int,
    subuser_update: schemas.SubUserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    subuser = db.query(models.SubUser).filter(
        models.SubUser.id == subuser_id,
        models.SubUser.parent_user_id == current_user.id
    ).first()
    
    if not subuser:
        raise HTTPException(status_code=404, detail="Alumno/a no encontrado/a")
        
    subuser.name = subuser_update.name
    db.commit()
    db.refresh(subuser)
    return subuser
