# PharmaLogix

PharmaLogix is a comprehensive web application designed with Django to streamline and enhance the management of pharmaceutical logistics.

## Key Features

- **Inventory Management**: Efficiently track and manage your pharmaceutical inventory.
- **Order Tracking**: Monitor and manage orders seamlessly.
- **Supplier Management**: Maintain and manage supplier information and interactions.
- **User Authentication and Authorization**: Secure user access with robust authentication and role-based authorization.
- **Barcode Scanning**: Simplify product identification and management with integrated barcode scanning.
- **Sales Metrics and Reporting**: Gain insights with detailed sales metrics and reporting tools.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/karar-hayder/PharmaLogix.git
    ```

2. Navigate to the project directory:

    ```bash
    cd PharmaLogix
    ```

3. Create a virtual environment:

    ```bash
    python -m venv env
    ```

4. Activate the virtual environment:
    - On Windows:

        ```bash
        .\env\Scripts\activate
        ```

    - On macOS/Linux:

        ```bash
        source env/bin/activate
        ```

5. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

6. Create a `.env` file in the `PharmaLogix` directory and set the necessary environment variables:

    ```plaintext
    DEBUG=True
    ADMIN_PAGE="admin/"
    DJANGO_SECERET='your secret'
    ALLOWED_HOSTS=*
    CSRF_TRUSTED_ORIGINS=*

    DB_HOST=your host
    DB_NAME=name 
    DB_USER=user 
    DB_PASSWORD=password 
    DB_PORT=5432
    ```

7. Apply the migrations:

    ```bash
    python manage.py migrate
    ```

8. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

9. Run the development server:

    ```bash
    python manage.py runserver
    ```

## Usage

1. Open your web browser and navigate to `http://127.0.0.1:8000/`.
2. Log in using the superuser credentials you created.
3. Begin managing your pharmaceutical logistics efficiently.

## Contributing

We welcome contributions! If you have suggestions or improvements, please open an issue or submit a pull request.

## License

This project is proprietary. All rights to the code are reserved. You must obtain explicit permission from the author to use, distribute, or modify any part of this project. For more details, please contact the author.

## Contact

For any inquiries, please reach out to [Karar Haider](mailto:kararhaider.pro@gmail.com).
