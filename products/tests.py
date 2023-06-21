from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import Seller, User
from products.models import Product, Review


class BaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller_user = User.objects.create_user(
            "seller@naver.com", "test_seller", "password"
        )
        cls.seller_user_data = {"email": "seller@naver.com", "password": "password"}

        cls.user = User.objects.create_user(
            "testuser@naver.com", "test_user", "password"
        )
        cls.user_data = {"email": "testuser@naver.com", "password": "password"}

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

    def setUp(self):
        self.seller_user_access_token = self.client.post(
            reverse("login"), self.seller_user_data
        ).data["access"]

        self.user_access_token = self.client.post(
            reverse("login"), self.user_data
        ).data["access"]


class ProductCreateTest(BaseTestCase):
    """상품 등록 테스트"""

    def test_fail_if_not_logged_in(self):
        url = reverse("product-list")
        response = self.client.post(url, self.product_data[0])
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Product.objects.count(), 0)

    def test_fail_if_not_seller(self):
        product_data = self.product_data[0]
        response = self.client.post(
            reverse("product-list"),
            product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 0)

    def test_fail_if_not_approved_seller(self):
        product_data = self.product_data[0]
        response = self.client.post(
            reverse("product-list"),
            product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 0)

    def test_success_if_approved_seller(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        product_data = self.product_data[0]
        response = self.client.post(
            reverse("product-list"),
            product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().name, product_data["name"])
        self.assertEqual(Product.objects.first().content, product_data["content"])


class ProductListTest(BaseTestCase):
    """상품 리스트 조회 테스트"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.seller_user2 = User.objects.create_user(
            "seller2@naver.com", "test_seller", "password"
        )
        cls.seller2 = Seller.objects.create(
            user=cls.seller_user2,
            company_name="test company2",
            business_number="012345",
            bank_name="test bank",
            account_number="123456",
            business_owner_name="test business owner",
            account_holder="test account holder",
            contact_number="234567",
        )

    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            seller=self.seller_user.user_seller, **self.product_data[0]
        )
        self.product2 = Product.objects.create(
            seller=self.seller2, **self.product_data[1]
        )

    def test_success_if_not_user_id(self):
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], self.product_data[0]["name"])

    def test_success_if_user_id(self):
        url = reverse("seller-product-list", kwargs={"user_id": self.seller_user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.product_data[1]["name"])
        self.assertEqual(response.data[0]["seller"], self.seller_user2.user_seller.id)

    def test_fail_if_user_not_seller(self):
        url = reverse("seller-product-list", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ProductDetailTest(BaseTestCase):
    """상품 상세 조회 테스트"""

    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            seller=self.seller_user.user_seller, **self.product_data[0]
        )

    def test_success_retrieve(self):
        url = reverse("product-detail", kwargs={"pk": self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.product_data[0]["name"])
        self.assertEqual(response.data["seller"], self.product.seller.id)


class ProductUpdateTest(BaseTestCase):
    """상품 수정 테스트"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.seller_user2 = User.objects.create_user(
            "seller2@naver.com", "test_seller", "password"
        )
        cls.seller2 = Seller.objects.create(
            user=cls.seller_user2,
            company_name="test company2",
            business_number="012345",
            bank_name="test bank",
            account_number="123456",
            business_owner_name="test business owner",
            account_holder="test account holder",
            contact_number="234567",
        )

    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            seller=self.seller_user.user_seller, **self.product_data[0]
        )
        self.product2 = Product.objects.create(
            seller=self.seller2, **self.product_data[1]
        )
        self.product_update_data = self.product_data[2]

    def test_fail_if_not_logged_in(self):
        url = reverse("product-detail", kwargs={"pk": self.product.id})
        response = self.client.put(url, self.product_update_data)
        self.assertEqual(response.status_code, 401)

    def test_fail_if_not_seller(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        # print("\ntest_fail_if_not_seller:", response.data)
        self.assertEqual(response.status_code, 403)

    def test_fail_if_not_approved_seller(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_fail_if_not_approved_seller:", response.data)
        self.assertEqual(response.status_code, 403)

    def test_fail_if_not_product_owner(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product2.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_fail_if_not_product_owner:", response.data)
        self.assertEqual(response.status_code, 403)

    def test_success_if_approved_seller(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_success_if_approved_seller:", response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.first().name, self.product_update_data["name"])
        self.assertEqual(
            Product.objects.first().content, self.product_update_data["content"]
        )


class ProductDeleteTest(BaseTestCase):
    """상품 삭제 테스트"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.seller_user2 = User.objects.create_user(
            "seller2@naver.com", "test_seller", "password"
        )
        cls.seller2 = Seller.objects.create(
            user=cls.seller_user2,
            company_name="test company2",
            business_number="012345",
            bank_name="test bank",
            account_number="123456",
            business_owner_name="test business owner",
            account_holder="test account holder",
            contact_number="234567",
        )

    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            seller=self.seller, **self.product_data[0]
        )
        self.product2 = Product.objects.create(
            seller=self.seller, **self.product_data[1]
        )
        self.product3 = Product.objects.create(
            seller=self.seller2, **self.product_data[2]
        )

    def test_fail_if_not_logged_in(self):
        url = reverse("product-detail", kwargs={"pk": self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_fail_if_not_seller(self):
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        # print("\ntest_fail_if_not_seller:", response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 3)

    def test_fail_if_not_approved_seller(self):
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_fail_if_not_approved_seller:", response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 3)

    def test_success_if_approved_seller(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_success_if_approved_seller:", response.data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Product.objects.count(), 2)
