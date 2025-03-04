


from fastapi import APIRouter, Depends, HTTPException
from ..models import Contacts, User
from ..Schemas import contacts, user
from ..database import database
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..oauth2 import get_current_user
import logging
from ..Schemas.contacts import ContactRead
from ..models.Contacts import Contact  # Import the Contact model
from fastapi import UploadFile, File, HTTPException, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import csv
from io import StringIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from io import StringIO
import csv
import json

router = APIRouter(tags=['Contacts'])

@router.post("/contacts/csv/")
async def bulk_import_contacts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

    content = (await file.read()).decode("utf-8")
    csv_reader = csv.DictReader(StringIO(content))

    contacts_to_create = []
    duplicate_records = []

    for row in csv_reader:
        email = row.get("email")
        phone = row.get("phone")
        name = row.get("name")
        tags = row.get("tags", "")

        # Validate required fields
        if not phone or not name:
            duplicate_records.append(row)
            continue

        # Parse and normalize tags into a list
        tags_list = []
        try:
            if tags:
                # Try to parse JSON if provided
                parsed_tags = json.loads(tags)
                if isinstance(parsed_tags, dict):
                    # Convert dict to a list of values
                    tags_list = list(parsed_tags.values())
                elif isinstance(parsed_tags, list):
                    # Directly use if already a list
                    tags_list = parsed_tags
                elif isinstance(parsed_tags, str):
                    # Split comma-separated string into a list
                    tags_list = [tag.strip() for tag in parsed_tags.split(",")]
                else:
                    raise ValueError("Invalid tags format.")
            else:
                tags_list = []
        except (json.JSONDecodeError, ValueError) as e:
            duplicate_records.append(row)
            continue

        # Check for existing contact
        existing_contact_query = select(Contacts.Contact).filter(
            Contacts.Contact.user_id == get_current_user.id,
            (Contacts.Contact.phone == phone) |
            (Contacts.Contact.email == email if email else False)
        )
        existing_contact = await db.execute(existing_contact_query)
        existing_contact = existing_contact.scalars().first()

        if existing_contact:
            duplicate_records.append(
                    Contacts.Contact(
                    user_id=get_current_user.id,
                    name=name,
                    email=email,
                    phone=phone,
                    tags=tags_list  # Pass tags as a list
                )
            )
        else:
            contacts_to_create.append(
                Contacts.Contact(
                    user_id=get_current_user.id,
                    name=name,
                    email=email,
                    phone=phone,
                    tags=tags_list  # Pass tags as a list
                )
            )


    return {
        "message": f"{len(contacts_to_create)} contacts to be imported",
        "contacts": contacts_to_create,
        "duplicates": duplicate_records,
    }



@router.post("/contacts/bulk_import/")
async def bulk_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

    content = (await file.read()).decode("utf-8")
    csv_reader = csv.DictReader(StringIO(content))

    contacts_to_create = []
    duplicate_records = []

    for row in csv_reader:
        email = row.get("email")
        phone = row.get("phone")
        name = row.get("name")
        tags = row.get("tags", "")

        # Validate required fields
        if not phone or not name:
            duplicate_records.append(row)
            continue

        # Parse and normalize tags into a list
        tags_list = []
        try:
            if tags:
                # Try to parse JSON if provided
                parsed_tags = json.loads(tags)
                if isinstance(parsed_tags, dict):
                    # Convert dict to a list of values
                    tags_list = list(parsed_tags.values())
                elif isinstance(parsed_tags, list):
                    # Directly use if already a list
                    tags_list = parsed_tags
                elif isinstance(parsed_tags, str):
                    # Split comma-separated string into a list
                    tags_list = [tag.strip() for tag in parsed_tags.split(",")]
                else:
                    raise ValueError("Invalid tags format.")
            else:
                tags_list = []
        except (json.JSONDecodeError, ValueError) as e:
            duplicate_records.append(row)
            continue

        # Check for existing contact
        existing_contact_query = select(Contacts.Contact).filter(
            Contacts.Contact.user_id == get_current_user.id,
            (Contacts.Contact.phone == phone) |
            (Contacts.Contact.email == email if email else False)
        )
        existing_contact = await db.execute(existing_contact_query)
        existing_contact = existing_contact.scalars().first()

        if existing_contact:
            duplicate_records.append(
                     Contacts.Contact(
                    user_id=get_current_user.id,
                    name=name,
                    email=email,
                    phone=phone,
                    tags=tags_list  # Pass tags as a list
                )
            )
        else:
            contacts_to_create.append(
                Contacts.Contact(
                    user_id=get_current_user.id,
                    name=name,
                    email=email,
                    phone=phone,
                    tags=tags_list  # Pass tags as a list
                )
            )

    # Insert valid contacts
    db.add_all(contacts_to_create)
    await db.commit()

    return {
        "message": f"{len(contacts_to_create)} contacts imported successfully.",
        "contacts": contacts_to_create,
        "duplicates": duplicate_records,
    }




@router.post("/contacts/", response_model=contacts.ContactRead)
async def create_contact(
    contact: contacts.ContactCreate,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    existing_contact = await db.execute(
        select(Contacts.Contact).filter(
            Contacts.Contact.user_id == get_current_user.id,
            (Contacts.Contact.email == contact.email) | (Contacts.Contact.phone == contact.phone)
        )
    )
    existing_contact = existing_contact.scalars().first()

    if existing_contact:
        raise HTTPException(
            status_code=400, detail="Contact with this email or phone already exists"
        )

    db_contact = Contacts.Contact(
        user_id=get_current_user.id,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        tags=contact.tags
    )
    
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact




@router.get("/contacts/", response_model=list[contacts.ContactRead])
async def read_contacts(
    skip: int = 0,
    limit: int = 10,
    tag: str = None,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    # Start building the query
    query = select(Contacts.Contact).filter(Contacts.Contact.user_id == get_current_user.id)
    
    # Apply tag filter if provided
    if tag:
        query = query.filter(Contacts.Contact.tags.contains([tag]))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute the query
    result = await db.execute(query)

    # Fetch all contacts
    contacts = result.scalars().all()

    logging.info(contacts)  # Log the contacts
    return contacts


@router.get("/contacts-filter/", response_model=List[ContactRead])
async def read_contacts(
    skip: int = 0,
    limit: int = 10,
    tag: Optional[str] = None,
    sort_by: str = 'updated_at',
    order: str = 'desc',
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    query = await db.execute(
        select(Contact).filter(Contact.user_id == get_current_user.id)
    )
    contacts_query = query.scalars()
    
    if tag:
        contacts_query = contacts_query.filter(Contact.tags.contains([tag]))

    if sort_by == 'updated_at':
        contacts_query = contacts_query.order_by(Contact.updated_at.desc() if order == 'desc' else Contact.updated_at.asc())
    elif sort_by == 'created_at':
        contacts_query = contacts_query.order_by(Contact.created_at.desc() if order == 'desc' else Contact.created_at.asc())

    contacts = contacts_query.offset(skip).limit(limit).all()
    return contacts

@router.get("/contacts/{phone_no}", response_model=contacts.ContactRead)
async def read_contact(
    phone_no: str,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    result = await db.execute(
        select(Contacts.Contact).filter(
            Contacts.Contact.phone == phone_no,
            Contacts.Contact.user_id == get_current_user.id
        )
    )
    contact = result.scalars().first()

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.delete("/contacts/{phone}")
async def delete_contact(
    phone: str,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    result = await db.execute(
        select(Contacts.Contact).filter(
            Contacts.Contact.phone == phone,
            Contacts.Contact.user_id == get_current_user.id
        )
    )
    contact = result.scalars().first()

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.delete(contact)
    await db.commit()
    return {"ok": True}

@router.put("/contacts/{contact_id}", response_model=contacts.ContactRead)
async def update_contact(
    contact_id: int,
    contact: contacts.ContactCreate,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    result = await db.execute(
        select(Contacts.Contact).filter(
            Contacts.Contact.id == contact_id,
            Contacts.Contact.user_id == get_current_user.id
        )
    )
    db_contact = result.scalars().first()

    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    existing_contact = await db.execute(
        select(Contacts.Contact).filter(
            (Contacts.Contact.id != contact_id) & 
            (Contacts.Contact.user_id == get_current_user.id) & 
            ((Contacts.Contact.email == contact.email) | (Contacts.Contact.phone == contact.phone))
        )
    )
    existing_contact = existing_contact.scalars().first()

    if existing_contact:
        raise HTTPException(
            status_code=400, detail="Contact with this email or phone already exists"
        )
    
    for key, value in contact.model_dump().items():
        setattr(db_contact, key, value)
    
    await db.commit()
    await db.refresh(db_contact)
    return db_contact

@router.get("/contacts-filter/filter", response_model=List[contacts.ContactRead])
async def filter_contacts_by_tags(
    tag_key: str,
    tag_value: str,
    db: AsyncSession = Depends(database.get_db),
    get_current_user: user.newuser = Depends(get_current_user)
):
    search_tag = f"{tag_key}:{tag_value}"
    
    # Query to filter contacts that have the matching tag in the list
    result = await db.execute(
        select(Contacts.Contact).filter(
            Contacts.Contact.user_id == get_current_user.id,
            Contacts.Contact.tags.op('@>')([f"{search_tag}"])
        )
    )
    filtered_contacts = result.scalars().all()

    if not filtered_contacts:
        raise HTTPException(status_code=404, detail="No contacts found with the specified tag")
    
    return filtered_contacts
