from rest_framework import serializers

from logistic.models import Product, StockProduct, Stock


class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=60)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description']



class ProductPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = StockProduct
        fields = ['product', 'quantity', 'price']


class StockSerializer(serializers.ModelSerializer):
    positions = ProductPositionSerializer(many=True)

    class Meta:
        model = Stock
        fields = ['address', 'positions']

    def validate_positions(self, value):
        if not value:
            raise serializers.ValidationError('Не указаны позиции товара на складе')
        position_ids = [item['product'].id for item in value]
        if len(position_ids) != len(set(position_ids)):
            raise serializers.ValidationError('Дублируются позиции товара на складе')
        return value


    def create(self, validated_data):
        positions = validated_data.pop('positions')
        stock = super().create(validated_data)
        StockProduct.objects.bulk_create([StockProduct(stock=stock,
                                                       product=position['product'],
                                                       quantity=position['quantity'],
                                                       price=position['price']) for position in positions])
        return stock

    def update(self, instance, validated_data):
        positions = validated_data.pop('positions')
        stock = super().update(instance, validated_data)
        for position in positions:
            product = position.pop('product')
            obj, created = StockProduct.objects.update_or_create(product=product, stock=stock, defaults=position)

            # long option
            # try:
            #     present_position = StockProduct.objects.get(product=position['product'].id, stock=stock.id)
            #     present_position.quantity = position['quantity']
            #     present_position.price = position['price']
            #     present_position.save()
            # except ObjectDoesNotExist:
            #     new_position = StockProduct.objects.create(stock=stock,
            #                                                product=position['product'],
            #                                                quantity=position['quantity'],
            #                                                price=position['price'])

        return stock
