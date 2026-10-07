from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class Customer:
    username: str = field(default_factory=lambda: f"qa_{uuid4().hex[:16]}")
    password: str = field(default_factory=lambda: f"Qa!{uuid4().hex[:16]}")

    def form(self) -> dict[str, str]:
        return {
            "customer.firstName": "Automation", "customer.lastName": "Engineer",
            "customer.address.street": "123 Test Street", "customer.address.city": "Testville",
            "customer.address.state": "CA", "customer.address.zipCode": "90210",
            "customer.phoneNumber": "5551234567", "customer.ssn": "123456789",
            "customer.username": self.username, "customer.password": self.password,
            "repeatedPassword": self.password,
        }
