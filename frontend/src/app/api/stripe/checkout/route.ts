import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { stripe } from '@/lib/stripe';
import { prisma } from '@/lib/prisma';

export async function POST(req: Request) {
  try {
    const session = await getServerSession();
    if (!session?.user?.email) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { plan } = await req.json();

    const productId = plan === 'pro' 
      ? process.env.POLAR_PRO_PRODUCT_ID 
      : process.env.POLAR_STARTER_PRODUCT_ID;

    if (!productId) {
      return NextResponse.json({ error: 'Product ID not configured' }, { status: 500 });
    }

    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // Call Polar API to create checkout session
    const response = await fetch('https://api.polar.sh/v1/checkouts/custom/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.POLAR_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id: productId,
        customer_email: user.email,
        customer_name: user.name || undefined,
        success_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/dashboard?success=true`,
        metadata: {
          userId: user.id.toString(),
          plan: plan,
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Polar error response:', errorText);
      return NextResponse.json({ error: 'Failed to create Polar checkout' }, { status: 500 });
    }

    const data = await response.json();

    return NextResponse.json({ url: data.url });
  } catch (error) {
    console.error('Polar error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
