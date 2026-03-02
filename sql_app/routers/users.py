# Create
@router.post("/users", response_model=schemas.User) 
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user(db=db, user=user)

@app.post("/conferencerooms",response_model=schemas.ConferenceRoom)
async def create_conferenceroom(conferenceroom: schemas.ConferenceRoomCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_conferenceroom(db = db, conferenceroom = conferenceroom)

@app.post("/bookings",response_model=schemas.Booking)
async def create_booking(booking: schemas.BookingCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_booking(db = db, booking = booking)

# Read
@app.get("/users", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_users(db, skip=skip, limit=limit)

@app.get("/conferencerooms", response_model = List[schemas.ConferenceRoom])
async def read_conferencerooms(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_conferencerooms(db, skip=skip, limit=limit)

@app.get("/bookings", response_model = List[schemas.Booking])
async def read_bookings(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_bookings(db, skip=skip, limit=limit)

# Update
@app.put("/users/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    return await crud.update_user(db=db, user_id=user_id, user=user)

@app.put("/conferencerooms/{conferenceroom_id}", response_model=schemas.ConferenceRoom)
async def update_conferenceroom(conferenceroom_id: int, conferenceroom: schemas.ConferenceRoomUpdate, db: AsyncSession = Depends(get_db)):
    return await crud.update_conferenceroom(db=db, conferenceroom_id=conferenceroom_id, conferenceroom=conferenceroom)

@app.put("/bookings/{booking_id}", response_model=schemas.Booking)
async def update_booking(booking_id: int, booking: schemas.BookingUpdate, db: AsyncSession = Depends(get_db)):
    return await crud.update_booking(db=db, booking_id=booking_id, booking=booking) 

# Delete
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.delete_user(db=db, user_id=user_id)  

@app.delete("/conferencerooms/{conferenceroom_id}")
async def delete_conferenceroom(conferenceroom_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.delete_conferenceroom(db=db, conferenceroom_id=conferenceroom_id)    

@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.delete_booking(db=db, booking_id=booking_id) 
