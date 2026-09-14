export function firstLabel(labels: string[]): string {
  const label = labels[0];
  if (label === undefined) throw new Error('At least one label is required');
  return label.toUpperCase();
}
