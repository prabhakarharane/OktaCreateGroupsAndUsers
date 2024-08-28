import requests
import json
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random
import string

# Replace these variables with your actual Okta details
OKTA_DOMAIN = '<your-domain>'  # Only the domain
API_TOKEN = '<your-api-key>'  # Your API token
GROUPS_Count = 100
USERS_PER_GROUPS = 40
HEADERS = {
    'Authorization': f'SSWS {API_TOKEN}',
    'Content-Type': 'application/json',
}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup requests session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Function to generate a random email
def generate_random_email(domain='example.com'):
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f'user{random_string}@{domain}'

# Function to create a user
def create_user(email):
    url = f'https://{OKTA_DOMAIN}/api/v1/users?activate=true'
    payload = {
        "profile": {
            "firstName": "Test",
            "lastName": "User",
            "email": email,
            "login": email
        },
        "credentials": {
            "password": {"value": "Password123"}  # You should use a more secure password management strategy
        }
    }
    try:
        response = session.post(url, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"User {email} created successfully.")
        return response.json()['id']
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create user {email}. Error: {str(e)}")
        return None

# Function to retrieve a user's ID using their email address
def get_user_id_by_email(email):
    url = f'https://{OKTA_DOMAIN}/api/v1/users'
    params = {'filter': f'profile.email eq "{email}"'}  # Use filter to search by email
    try:
        response = session.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        users = response.json()
        if users:
            return users[0]['id']  # Return the first matched user's ID
        else:
            logging.error(f"No user found with email: {email}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve user ID for email {email}. Error: {str(e)}")
        return None

# Function to add a user to a group using their user ID
def add_user_to_group(group_id, user_email):
    user_id = get_user_id_by_email(user_email)
    if user_id is None:
        user_id = create_user(user_email)  # Create user if not found
        if user_id is None:
            logging.error(f"Cannot add user {user_email} to group. User creation failed.")
            return

    url = f'https://{OKTA_DOMAIN}/api/v1/groups/{group_id}/users/{user_id}'
    try:
        response = session.put(url, headers=HEADERS)
        response.raise_for_status()
        logging.info(f"User {user_email} added to group successfully.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logging.error(f"Failed to add user {user_email} to group due to insufficient permissions. Check API token permissions.")
        else:
            logging.error(f"Failed to add user {user_email} to group. Error: {str(e)}")

# Function to create multiple groups and add new users to each
def create_groups_and_add_users(number_of_groups, users_per_group=USERS_PER_GROUPS):
    for i in range(111, number_of_groups + 1):
        group_name = f"QAGroup {i}"
        group_id = create_group(group_name)
        if group_id:
            for _ in range(users_per_group):
                user_email = generate_random_email()
                add_user_to_group(group_id, user_email)

# Function to create a group
def create_group(group_name):
    url = f'https://{OKTA_DOMAIN}/api/v1/groups'
    payload = {
        "profile": {
            "name": group_name,
            "description": f"This is the group named {group_name}"
        }
    }
    try:
        response = session.post(url, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Group {group_name} created successfully.")
        return response.json()['id']
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create group {group_name}. Error: {str(e)}")
        return None

# Number of groups to create
NUMBER_OF_GROUPS = GROUPS_Count

create_groups_and_add_users(NUMBER_OF_GROUPS)
