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

    # 비로그인 시 등록 실패
    def test_fail_if_not_logged_in(self):
        url = reverse("product-list")
        response = self.client.post(url, self.product_data[0])
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Product.objects.count(), 0)

    # Seller 객체가 없을 때 등록 실패
    def test_fail_if_not_seller(self):
        product_data = self.product_data[0]
        response = self.client.post(
            reverse("product-list"),
            product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 0)

    # is_seller가 False일 때, 등록 실패
    def test_fail_if_not_approved_seller(self):
        product_data = self.product_data[0]
        response = self.client.post(
            reverse("product-list"),
            product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 0)

    # 등록 성공
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

    # 전체 목록 조회 성공
    def test_success_if_not_user_id(self):
        url = reverse("product-list")
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], self.product_data[0]["name"])

    # 특정 판매자 상품 조회 성공
    def test_success_if_user_id(self):
        url = reverse("seller-product-list", kwargs={"user_id": self.seller_user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.product_data[1]["name"])
        self.assertEqual(response.data[0]["seller"], self.seller_user2.user_seller.id)

    # 판매자가 아닌 유저 id로 조회 시 실패
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

    # 상품이 없을 때 조회 실패
    def test_fail_if_not_product(self):
        response = self.client.get(reverse("product-detail", kwargs={"pk": 99}))
        self.assertEqual(response.status_code, 404)

    # 상품 상세 조회 성공
    def test_retrieve_success(self):
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

    # 해당 상품이 없을 때 수정 실패
    def test_fail_if_not_product(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": 99}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        self.assertEqual(response.status_code, 404)

    # 비로그인시 수정 실패
    def test_fail_if_not_logged_in(self):
        url = reverse("product-detail", kwargs={"pk": self.product.id})
        response = self.client.put(url, self.product_update_data)
        self.assertEqual(response.status_code, 401)

    # Seller 객체가 없을 때 수정 실패
    def test_fail_if_not_seller(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        # print("\n - test_fail_if_not_seller:", response.data)
        self.assertEqual(response.status_code, 403)

    # is_seller가 False일 때 수정 실패
    def test_fail_if_not_approved_seller(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\n - test_fail_if_not_approved_seller:", response.data)
        self.assertEqual(response.status_code, 403)

    # 자신의 상품이 아닐 때 수정 실패
    def test_fail_if_not_product_owner(self):
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product2.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\n - test_fail_if_not_product_owner:", response.data)
        self.assertEqual(response.status_code, 403)

    # 수정 성공
    def test_update_success(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            self.product_update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\n - test_success_if_approved_seller:", response.data)
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

    # 비로그인시 삭제 실패
    def test_fail_if_not_logged_in(self):
        url = reverse("product-detail", kwargs={"pk": self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    # Seller 객체가 없을 때 삭제 실패
    def test_fail_if_not_seller(self):
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        # print("\ntest_fail_if_not_seller:", response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 3)

    # is_seller가 False일 때 삭제 실패
    def test_fail_if_not_approved_seller(self):
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_fail_if_not_approved_seller:", response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 3)

    # 삭제 성공
    def test_delete_success(self):
        self.seller_user.is_seller = True
        self.seller_user.save()
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.seller_user_access_token}",
        )
        # print("\ntest_success_if_approved_seller:", response.data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Product.objects.count(), 2)


# OrderedDict(
#     [
#         ("count", 2),
#         ("next", None),
#         ("previous", None),
#         (
#             "results",
#             [
#                 OrderedDict(
#                     [
#                         ("id", 2),
#                         ("sales", 0),
#                         ("likes", 0),
#                         ("stars", None),
#                         ("created_at", "2023-06-22T18:49:36.605239"),
#                         ("updated_at", "2023-06-22T18:49:36.605239"),
#                         ("name", "product test name2"),
#                         ("content", "product test introduction2"),
#                         ("price", 0),
#                         ("amount", 0),
#                         ("image", None),
#                         ("seller", 2),
#                         ("category", None),
#                     ]
#                 ),
#                 OrderedDict(
#                     [
#                         ("id", 1),
#                         ("sales", 0),
#                         ("likes", 0),
#                         ("stars", None),
#                         ("created_at", "2023-06-22T18:49:36.604240"),
#                         ("updated_at", "2023-06-22T18:49:36.604240"),
#                         ("name", "product test name1"),
#                         ("content", "product test introduction1"),
#                         ("price", 0),
#                         ("amount", 0),
#                         ("image", None),
#                         ("seller", 1),
#                         ("category", None),
#                     ]
#                 ),
#             ],
#         ),
#     ]
# )
