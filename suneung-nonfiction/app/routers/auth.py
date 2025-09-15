from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import json
from ..db_sql import get_db, Base, engine
from ..models import User, Submission
from ..schemas_auth import SignUpReq, LoginReq, TokenRes, MeRes, SubmissionRes
from ..auth_core import hash_password, verify_password, create_access_token, decode_access_token

Base.metadata.create_all(bind=engine)  # 최초 1회 테이블 생성

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

def get_current_user(db: Session = Depends(get_db),
                     cred: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not cred or not cred.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    username = decode_access_token(cred.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/signup", response_model=TokenRes, status_code=201)
def signup(req: SignUpReq, db: Session = Depends(get_db)):
    exists = db.query(User).filter((User.username == req.username)|(User.email == req.email)).first()
    if exists:
        raise HTTPException(400, "username/email already exists")
    user = User(username=req.username, email=req.email, password_hash=hash_password(req.password))
    db.add(user); db.commit()
    return TokenRes(access_token=create_access_token(req.username))

@router.post("/login", response_model=TokenRes)
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    return TokenRes(access_token=create_access_token(user.username))

@router.get("/me", response_model=MeRes)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = (db.query(Submission)
            .filter(Submission.user_id == user.id)
            .order_by(Submission.created_at.desc()).all())
    def _s(s: Submission) -> SubmissionRes:
        return SubmissionRes(
            id=s.id, item_id=s.item_id, choice_index=s.choice_index, correct=s.correct,
            explain=s.explain, evidence_sent_ids=json.loads(s.evidence_sent_ids_json or "[]"),
            created_at=s.created_at.isoformat(),
        )
    return MeRes(id=user.id, username=user.username, email=user.email,
                 submissions=[_s(x) for x in subs])
