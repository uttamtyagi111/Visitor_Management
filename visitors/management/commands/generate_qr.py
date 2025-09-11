import qrcode
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate static QR code for visitor registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://yourdomain.com/visitor',
            help='URL for visitor registration'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='visitor_qr_code.png',
            help='Output filename'
        )

    def handle(self, *args, **options):
        url = options['url']
        output = options['output']
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to media directory or specified path
        if not os.path.isabs(output):
            output = os.path.join(settings.MEDIA_ROOT, 'qr_codes', output)
            os.makedirs(os.path.dirname(output), exist_ok=True)
        
        img.save(output)
        
        self.stdout.write(
            self.style.SUCCESS(f'QR code saved to: {output}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'QR code points to: {url}')
        )