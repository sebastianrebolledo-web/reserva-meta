import unittest
from datetime import date, timedelta
from pydantic import ValidationError
from app.schemas.reservation import ReservationCreate, EquipmentItem
from app.api.v1.endpoints.reservations import create_reservation
import asyncio


class TestReservationSystem(unittest.TestCase):
    def test_date_calculation_and_domain_success(self):
        req_date = date.today() + timedelta(days=2)
        duration = 5
        payload = ReservationCreate(
            applicant_email="sebastian.rebolledo@grupotecfluid.com",
            kam_name="Sebastián Rebolledo",
            commercial_management="Minería",
            client_name="Minera Centinela",
            request_date=req_date,
            duration_days=duration,
            equipment_details=[
                EquipmentItem(name="Meta Quest 3 (128GB)", quantity=1),
                EquipmentItem(name="Controles Touch Plus", quantity=1),
            ],
            notes="Prueba de concepto gemelo digital"
        )

        expected_delivery = req_date + timedelta(days=duration)
        self.assertEqual(payload.delivery_date, expected_delivery)
        self.assertEqual(payload.applicant_email, "sebastian.rebolledo@grupotecfluid.com")

        # Test endpoint execution
        res = asyncio.run(create_reservation(payload))
        self.assertTrue(res.success)
        self.assertEqual(res.delivery_date, expected_delivery)
        self.assertIn("Meta Quest 3", res.equipment_summary)

    def test_invalid_email_domain_fails(self):
        req_date = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            ReservationCreate(
                applicant_email="usuario@gmail.com",
                kam_name="Juan Perez",
                commercial_management="Ventas",
                client_name="Cliente X",
                request_date=req_date,
                duration_days=3,
                equipment_details=[EquipmentItem(name="Meta Quest 3", quantity=1)]
            )
        self.assertIn("grupotecfluid.com", str(ctx.exception))

    def test_invalid_duration_days_fails(self):
        req_date = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            ReservationCreate(
                applicant_email="test@grupotecfluid.com",
                kam_name="Juan Perez",
                commercial_management="Ventas",
                client_name="Cliente X",
                request_date=req_date,
                duration_days=0,  # Minimo es 1
                equipment_details=[EquipmentItem(name="Meta Quest 3", quantity=1)]
            )


if __name__ == "__main__":
    unittest.main()
