from pydantic import BaseModel


class TransactionInfo(BaseModel):
    destination: str
    status: str
    amount: float
