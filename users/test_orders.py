from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import (
    CartItem,
    PhoneVerification,
    Point,
    Seller,
    User,
    Bill,
    OrderItem,
    StatusCategory,
    PointType,
)
from products.models import Product, Review
from json import dumps
from django.core.management import call_command


class BaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller_user = User.objects.create_user(
            "seller@naver.com", "testseller", "!@#password123"
        )
        cls.seller_user_data = {
            "email": "seller@naver.com",
            "password": "!@#password123",
        }

        cls.user = User.objects.create_user(
            "testuser@naver.com", "testuser", "!@#password123"
        )
        cls.user_data = {"email": "testuser@naver.com", "password": "!@#password123"}
        cls.phone = PhoneVerification.objects.create(
            user=cls.user,
            phone_number="01012345678",
            verification_numbers="1234",
            is_verified=True,
        )

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
                "amount": 100,
            },
            {
                "name": "product test name2",
                "content": "product test introduction2",
                "amount": 100,
            },
            {
                "name": "product test name3",
                "content": "product test introduction3",
                "amount": 100,
            },
        ]

        cls.product = Product.objects.create(seller=cls.seller, **cls.product_data[0])
        cls.product2 = Product.objects.create(seller=cls.seller, **cls.product_data[1])
        cls.product3 = Product.objects.create(seller=cls.seller, **cls.product_data[2])
        # cls.status_one = StatusCategory.objects.create(name="결제대기")
        # cls.status_two = StatusCategory.objects.create(name="주문확인")
        # cls.status_three = StatusCategory.objects.create(name="배송준비중")
        # cls.status_four = StatusCategory.objects.create(name="발송완료")
        # cls.status_five = StatusCategory.objects.create(name="배송완료")
        # cls.status_six = StatusCategory.objects.create(name="구매확정")
        # cls.point_one = PointType.objects.create(title="출석")
        # cls.point_two = PointType.objects.create(title="텍스트리뷰")
        # cls.point_three = PointType.objects.create(title="포토리뷰")
        # cls.point_four = PointType.objects.create(title="구매")
        # cls.point_five = PointType.objects.create(title="충전")
        # cls.point_six = PointType.objects.create(title="사용")
        # cls.point_seven = PointType.objects.create(title="결제")
        # cls.point_eight = PointType.objects.create(title="정산")
        # cls.point_nine = PointType.objects.create(title="환불")

    def setUp(self):
        self.seller_user_access_token = self.client.post(
            reverse("login"), self.seller_user_data
        ).data["access"]

        self.user_access_token = self.client.post(
            reverse("login"), self.user_data
        ).data["access"]


class CartItemCreateTest(BaseTestCase):
    """장바구니 생성 테스트"""

    def test_create_cart_item_sucess(self):
        data = {"user": self.user.pk, "product": self.product.pk, "amount": 1}
        response = self.client.post(
            reverse("cart_view"),
            data,
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 200)


class CartItemListTest(BaseTestCase):
    """장바구니 목록 조회 테스트"""

    def test_list_cart_items_sucess(self):
        cart = CartItem.objects.create(
            user=self.user,
            product=self.product,
            amount=1,
        )
        response = self.client.get(
            reverse("cart_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 200)


class CartItemPatchTest(BaseTestCase):
    """장바구니 수량 변경 테스트"""

    def test_patch_cart_items_sucess(self):
        cart = CartItem.objects.create(
            user=self.user,
            product=self.product,
            amount=1,
        )
        response = self.client.put(
            reverse(
                "cart_detail_view",
                kwargs={"pk": cart.id},
            ),
            data={"amount": 3},
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("amount"), 3)


class CartItemDeleteTest(BaseTestCase):
    """장바구니 삭제"""

    def test_delete_cart_items_sucess(self):
        cart = CartItem.objects.create(
            user=self.user,
            product=self.product,
            amount=1,
        )
        response = self.client.delete(
            reverse("cart_delete_view") + f"?cart_id={cart.id}",
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(CartItem.objects.all().exists(), False)


class BillCreateTest(BaseTestCase):
    """주문내역(주문서) 생성"""

    def test_create_bill_sucess(self):
        data = {
            "new_delivery": True,
            "address": "address",
            "detail_address": "detailaddress",
            "recipient": "recipient",
            "postal_code": "12345",
        }
        response = self.client.post(
            reverse("bill_view"),
            data=dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 201)


class BillListTest(BaseTestCase):
    """주문내역 목록 조회"""

    def setUp(self):
        super().setUp()
        self.bill = Bill.objects.create(
            user=self.user,
            address="address",
            detail_address="detailaddress",
            recipient="recipient",
            postal_code="12345",
            is_paid=True,
        )
        self.bill2 = Bill.objects.create(
            user=self.user,
            address="address",
            detail_address="detailaddress",
            recipient="recipient",
            postal_code="12345",
            is_paid=True,
        )
        self.bill3 = Bill.objects.create(
            user=self.user,
            address="address",
            detail_address="detailaddress",
            recipient="recipient",
            postal_code="12345",
            is_paid=True,
        )

    def test_list_bill_sucess(self):
        response = self.client.get(
            reverse("bill_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


class OrderCreateTest(BaseTestCase):
    """주문 생성 테스트"""

    def setUp(self):
        super().setUp()
        call_command("loaddata", "json_data/status.json")
        call_command("loaddata", "json_data/point.json")
        self.cart = CartItem.objects.create(
            user=self.user,
            product=self.product,
            amount=1,
        )
        self.cart2 = CartItem.objects.create(
            user=self.user,
            product=self.product2,
            amount=2,
        )
        self.cart3 = CartItem.objects.create(
            user=self.user,
            product=self.product3,
            amount=3,
        )
        point_type = PointType.objects.get(pk=1)
        self.user_point = Point.objects.create(
            user=self.user, point=100000, point_type=point_type
        )

    def test_create_order_sucess(self):
        bill = Bill.objects.create(
            user=self.user,
            address="address",
            detail_address="detailaddress",
            recipient="recipient",
            postal_code="12345",
            is_paid=False,
        )
        response = self.client.post(
            reverse("order_create_view", kwargs={"bill_id": bill.id})
            + f"?cart_id={self.cart.id}&{self.cart2.id}&{self.cart3.id}",
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, 201)
