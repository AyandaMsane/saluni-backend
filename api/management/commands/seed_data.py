from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Provider, Service, UserProfile


class Command(BaseCommand):
    help = "Seeds initial beauty providers and services into the database"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        Service.objects.all().delete()
        Provider.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Creating test users...")
        # Create professional users
        glow_user = User.objects.create_user(
            username="0821111111",
            password="Password123",
            first_name="Glow",
            last_name="Owner",
            email="glow@example.com"
        )
        UserProfile.objects.create(user=glow_user, role="professional")

        nail_user = User.objects.create_user(
            username="0822222222",
            password="Password123",
            first_name="Nail",
            last_name="Owner",
            email="nail@example.com"
        )
        UserProfile.objects.create(user=nail_user, role="professional")

        hair_user = User.objects.create_user(
            username="0823333333",
            password="Password123",
            first_name="Hair",
            last_name="Owner",
            email="hair@example.com"
        )
        UserProfile.objects.create(user=hair_user, role="professional")

        # Create a client user for testing
        client_user = User.objects.create_user(
            username="0824444444",
            password="Password123",
            first_name="Jane",
            last_name="Client",
            email="jane@example.com"
        )
        UserProfile.objects.create(user=client_user, role="client")

        self.stdout.write("Creating providers...")
        glow_studio = Provider.objects.create(
            user=glow_user,
            name="Glow Studio",
            slug="glow-studio",
            owner_name="Glow Owner",
            whatsapp_number="27821111111",
            specialty="Hair, Nails, Lashes",
            location="Sandton",
            is_active=True,
            status="approved",
            is_featured=True,
            bio="A polished beauty studio for hair styling, detailed nails, and soft glam finishing.",
        )

        nail_house = Provider.objects.create(
            user=nail_user,
            name="Nail House",
            slug="nail-house",
            owner_name="Nail Owner",
            whatsapp_number="27822222222",
            specialty="Nails, Brows",
            location="Rosebank",
            is_active=True,
            status="approved",
            is_featured=True,
            bio="Detail-led nail care with clean finishes, modern sets, and brow touch-ups.",
        )

        hair_lab = Provider.objects.create(
            user=hair_user,
            name="Hair Lab",
            slug="hair-lab",
            owner_name="Hair Owner",
            whatsapp_number="27823333333",
            specialty="Hair, Makeup",
            location="Bryanston",
            is_active=True,
            status="approved",
            is_featured=False,
            bio="A calm hair and makeup studio for protective styles, installs, washes, and event-ready beauty.",
        )


        self.stdout.write("Creating services for Glow Studio...")
        # Hair
        Service.objects.create(
            provider=glow_studio,
            name="Braids",
            category="Hair",
            description="Professional neat hair braiding.",
            duration_minutes=90,
            starting_price=420.00,
        )
        Service.objects.create(
            provider=glow_studio,
            name="Install",
            category="Hair",
            description="Flawless lace install.",
            duration_minutes=120,
            starting_price=550.00,
        )
        Service.objects.create(
            provider=glow_studio,
            name="Wash",
            category="Hair",
            description="Deep wash, treatment, and blow dry.",
            duration_minutes=30,
            starting_price=150.00,
        )
        # Nails
        Service.objects.create(
            provider=glow_studio,
            name="Acrylic Nails",
            category="Nails",
            description="Full set acrylic extensions.",
            duration_minutes=60,
            starting_price=320.00,
        )
        Service.objects.create(
            provider=glow_studio,
            name="Gel Overlay",
            category="Nails",
            description="Overlay gel polish on natural nails.",
            duration_minutes=45,
            starting_price=280.00,
        )
        # Lashes
        Service.objects.create(
            provider=glow_studio,
            name="Classic Eyelashes",
            category="Lashes",
            description="Perfect natural classic extensions.",
            duration_minutes=60,
            starting_price=350.00,
        )
        Service.objects.create(
            provider=glow_studio,
            name="Volume Eyelashes",
            category="Lashes",
            description="Dense full-volume lash extensions.",
            duration_minutes=90,
            starting_price=450.00,
        )

        self.stdout.write("Creating services for Nail House...")
        # Nails
        Service.objects.create(
            provider=nail_house,
            name="Acrylic Nails Set",
            category="Nails",
            description="Full set acrylic extensions.",
            duration_minutes=60,
            starting_price=300.00,
        )
        Service.objects.create(
            provider=nail_house,
            name="Gel Polish Overlay",
            category="Nails",
            description="High quality gel polish.",
            duration_minutes=45,
            starting_price=260.00,
        )
        Service.objects.create(
            provider=nail_house,
            name="Custom Nail Art",
            category="Nails",
            description="Custom creative nail art designs.",
            duration_minutes=30,
            starting_price=150.00,
        )
        # Brows
        Service.objects.create(
            provider=nail_house,
            name="Brow Shaping",
            category="Brows",
            description="Professional wax/tweeze brow shaping.",
            duration_minutes=30,
            starting_price=180.00,
        )
        Service.objects.create(
            provider=nail_house,
            name="Brow Tinting",
            category="Brows",
            description="Long-lasting natural brow tinting.",
            duration_minutes=30,
            starting_price=200.00,
        )

        self.stdout.write("Creating services for Hair Lab...")
        # Hair
        Service.objects.create(
            provider=hair_lab,
            name="Braids Styling",
            category="Hair",
            description="Neat protective braids styling.",
            duration_minutes=90,
            starting_price=400.00,
        )
        Service.objects.create(
            provider=hair_lab,
            name="Lace Install",
            category="Hair",
            description="Wig or weave install and style.",
            duration_minutes=120,
            starting_price=500.00,
        )
        Service.objects.create(
            provider=hair_lab,
            name="Hair Wash",
            category="Hair",
            description="Cleanse, condition, and dry.",
            duration_minutes=30,
            starting_price=150.00,
        )
        # Makeup
        Service.objects.create(
            provider=hair_lab,
            name="Soft Glam Makeup",
            category="Makeup",
            description="Subtle soft event makeup.",
            duration_minutes=60,
            starting_price=500.00,
        )
        Service.objects.create(
            provider=hair_lab,
            name="Full Glam Makeup",
            category="Makeup",
            description="Dramatic full camera-ready makeup.",
            duration_minutes=90,
            starting_price=700.00,
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with Users!"))

