from fastapi import FastAPI, Depends
from armasec import Armasec


app = FastAPI()
armasec = Armasec(
    domain="typerdrive-tutorial.us.auth0.com",
    audience="typerdrive-tutorial",
)


@app.get("/unsecured")
async def unsecured():
    return dict(message="Accessed unsecured endpoint!")


@app.get("/secured", dependencies=[Depends(armasec.lockdown())])
async def check_access():
    return dict(message="Accessed secured endpoint!")
