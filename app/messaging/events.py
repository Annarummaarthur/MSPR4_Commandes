# Événements liés aux commandes que cette API peut publier

# Événements Order
ORDER_CREATED = "order.created"
ORDER_UPDATED = "order.updated"
ORDER_STATUS_CHANGED = "order.status_changed"
ORDER_CANCELLED = "order.cancelled"
ORDER_SHIPPED = "order.shipped"
ORDER_DELIVERED = "order.delivered"

# Événements auxquels cette API peut s'abonner (provenant d'autres services)

# Événements Customer (provenant de l'API Customers)
CUSTOMER_CREATED = "customer.created"
CUSTOMER_UPDATED = "customer.updated"
CUSTOMER_DELETED = "customer.deleted"

# Événements Product (provenant de l'API Products)
PRODUCT_CREATED = "product.created"
PRODUCT_UPDATED = "product.updated"
PRODUCT_DELETED = "product.deleted"

# Mapping des événements pour le logging
EVENT_DESCRIPTIONS = {
    # Événements Orders
    ORDER_CREATED: "Nouvelle commande créée",
    ORDER_UPDATED: "Commande mise à jour",
    ORDER_STATUS_CHANGED: "Statut de commande changé",
    ORDER_CANCELLED: "Commande annulée",
    ORDER_SHIPPED: "Commande expédiée",
    ORDER_DELIVERED: "Commande livrée",
    # Événements Customer
    CUSTOMER_CREATED: "Nouveau client créé",
    CUSTOMER_UPDATED: "Client mis à jour",
    CUSTOMER_DELETED: "Client supprimé",
    # Événements Product
    PRODUCT_CREATED: "Nouveau produit créé",
    PRODUCT_UPDATED: "Produit mis à jour",
    PRODUCT_DELETED: "Produit supprimé",
}
