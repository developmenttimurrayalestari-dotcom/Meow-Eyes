export const TRY_ON_PRODUCT_TYPES = ['frame', 'package'];

export function isTryOnProduct(product) {
  return Boolean(product && !product.deleted_at && TRY_ON_PRODUCT_TYPES.includes(product.product_type));
}
