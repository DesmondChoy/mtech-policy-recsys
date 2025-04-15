// Utility to fetch customer UUIDs from the generated JSON file in public/
export async function fetchCustomerIds(): Promise<string[]> {
  const res = await fetch('/customer_ids.json');
  if (!res.ok) throw new Error('Failed to load customer IDs');
  return res.json();
}
