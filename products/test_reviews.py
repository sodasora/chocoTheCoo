from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import Seller, User
from products.models import Product, Review


class BaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller_user = User.objects.create_user(
            "seller@naver.com", "test_seller", "!@#password123"
        )
        cls.seller_user_data = {"email": "seller@naver.com", "password": "!@#password123"}

        cls.user = User.objects.create_user(
            "testuser@naver.com", "test_user", "!@#password123"
        )
        cls.user_data = {"email": "testuser@naver.com", "password": "!@#password123"}

        cls.seller = Seller.objects.create(
            user=cls.seller_user,
            company_name="test company",
            business_number="012345",
            bank_name="test bank",
            account_number="123456",
            business_owner_name="test business owner",
            account_holder="test account holder",
            contact_number="234567",
        )
        cls.user.is_active = True
        cls.seller_user.is_active = True
        cls.user.save()
        cls.seller_user.save()

        cls.product_data = [
            {
                "name": "product test name1",
                "content": "product test introduction1",
            },
            {
                "name": "product test name2",
                "content": "product test introduction2",
            },
            {
                "name": "product test name3",
                "content": "product test introduction3",
            },
        ]

        cls.review_data = [
            {
                "user": "user",
                "product": "product",
                "title": "title",
                "content": "content",
                "image": "image",
                "star": "star",
                "delivery_evaluation": "delivery_evaluation",
                "service_evaluation": "service_evaluation",
                "feedback_evaluation": "feedback_evaluation",
            }
        ]

    def setUp(self):
        self.seller_user_access_token = self.client.post(
            reverse("login"), self.seller_user_data
        ).data["access"]

        self.user_access_token = self.client.post(
            reverse("login"), self.user_data
        ).data["access"]


class ReviewCreateTest(BaseTestCase):
    pass


class ReviewListTest(BaseTestCase):
    pass


class ReviewDetailTest(BaseTestCase):
    pass


class ReviewUpdateTest(BaseTestCase):
    pass


class ReviewDeleteTest(BaseTestCase):
    pass
