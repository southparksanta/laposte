from app import app, db, Tracking

with app.app_context():
    trackings = Tracking.query.filter_by(status="En attente").all()
    count = 0
    for t in trackings:
        t.status = "En cours de livraison"
        count += 1
    db.session.commit()
    print(f"Updated {count} records.")
