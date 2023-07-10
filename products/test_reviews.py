from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import Seller, User, Bill, OrderItem, StatusCategory, PointType
from products.models import Product, Review


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
        cls.product = Product.objects.create(seller=cls.seller, **cls.product_data[0])
        cls.review_data = [
            {
                "user": cls.user,
                "product": cls.product,
                "title": "title",
                "content": "content",
                "image": "image",
                "star": "star",
                "delivery_evaluation": "delivery_evaluation",
                "service_evaluation": "service_evaluation",
                "feedback_evaluation": "feedback_evaluation",
            }
        ]
        cls.status_one = StatusCategory.objects.create(name="결제대기")
        cls.status_two = StatusCategory.objects.create(name="주문확인")
        cls.status_three = StatusCategory.objects.create(name="배송준비중")
        cls.status_four = StatusCategory.objects.create(name="발송완료")
        cls.status_five = StatusCategory.objects.create(name="배송완료")
        cls.status_six = StatusCategory.objects.create(name="구매확정")
        cls.point_one = PointType.objects.create(title="출석")
        cls.point_two = PointType.objects.create(title="텍스트리뷰")
        cls.point_three = PointType.objects.create(title="포토리뷰")
        cls.point_four = PointType.objects.create(title="구매")
        cls.point_five = PointType.objects.create(title="충전")
        cls.point_six = PointType.objects.create(title="사용")
        cls.point_seven = PointType.objects.create(title="결제")
        cls.point_eight = PointType.objects.create(title="정산")
        cls.point_nine = PointType.objects.create(title="환불")

    def setUp(self):
        self.seller_user_access_token = self.client.post(
            reverse("login"), self.seller_user_data
        ).data["access"]

        self.user_access_token = self.client.post(
            reverse("login"), self.user_data
        ).data["access"]

        self.product2 = Product.objects.create(
            seller=self.seller, **self.product_data[1]
        )
        self.bill = Bill.objects.create(
            user=self.user,
            address="address",
            detail_address="detailaddress",
            recipient="recipient",
            postal_code="12345",
            is_paid=True,
        )
        self.orderitem = OrderItem.objects.create(
            bill=self.bill,
            seller=self.seller,
            order_status=self.status_six,
            name="name",
            amount=1,
            price=1000,
            product_id=self.product.id,
        )


class ReviewCreateTest(BaseTestCase):
    """리뷰 생성 테스트"""
    def test_create_review_success(self):
        response = self.client.post(
            reverse("review_view", kwargs={"product_id": self.product.id}),
            data={
                "user": self.user,
                "product": self.product,
                "title": "Test review title",
                "content": "Test review content",
                "star": 5,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ReviewListTest(BaseTestCase):
    """리뷰 목록 조회 테스트"""
    def test_get_review_list_success(self):
        response = self.client.get(
            reverse("review_view", kwargs={"product_id": self.product.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReviewDetailTest(BaseTestCase):
    """리뷰 수정 테스트"""
    def test_put_review_detail_success(self):
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            title="Test review title",
            content="Test review content",
            star=5,
        )
        response = self.client.put(
            reverse(
                "review_detail_view",
                kwargs={"product_id": self.product.id, "pk": review.id},
            ),
            data={
                "user": self.user,
                "product": self.product,
                "title": "Test review title",
                "content": "Test review content modified",
                "star": 1,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.user_access_token}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("star"), 1)
