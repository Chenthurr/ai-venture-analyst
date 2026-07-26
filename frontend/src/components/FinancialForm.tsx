"use client";

import { useState } from "react";
import { Input, Button, SectionLabel } from "@/components/ui";

const FIELDS: { key: string; label: string; step?: string }[] = [
  { key: "monthly_revenue", label: "Monthly Revenue ($)" },
  { key: "monthly_cogs", label: "Monthly COGS ($)" },
  { key: "monthly_operating_expenses", label: "Monthly OpEx ($)" },
  { key: "cash_balance", label: "Cash Balance ($)" },
  { key: "new_customers_this_month", label: "New Customers (this month)" },
  { key: "total_customers", label: "Total Customers" },
  { key: "churned_customers_this_month", label: "Churned Customers (this month)" },
  { key: "sales_marketing_spend", label: "Sales & Marketing Spend ($)" },
  { key: "avg_revenue_per_account", label: "Avg Revenue Per Account ($/mo)" },
  { key: "avg_price_per_unit", label: "Avg Price Per Unit ($)" },
  { key: "avg_variable_cost_per_unit", label: "Avg Variable Cost Per Unit ($)" },
  { key: "fixed_costs_monthly", label: "Fixed Costs (Monthly, $)" },
  { key: "projected_annual_growth_rate", label: "Projected Annual Growth Rate (0-1)", step: "0.01" },
  { key: "discount_rate", label: "Discount Rate / WACC (0-1)", step: "0.01" },
  { key: "exit_multiple_revenue", label: "Exit Revenue Multiple (x)", step: "0.1" },
  { key: "years_to_exit", label: "Years to Exit" },
  { key: "anticipated_roi", label: "Anticipated ROI (x, VC Method)", step: "0.1" },
  { key: "investment_amount_requested", label: "Investment Amount Requested ($)" },
  { key: "industry_revenue_multiple", label: "Industry Revenue Multiple (comparables, x)", step: "0.1" },
];

const DEFAULTS: Record<string, number> = {
  monthly_revenue: 0,
  monthly_cogs: 0,
  monthly_operating_expenses: 0,
  cash_balance: 0,
  new_customers_this_month: 0,
  total_customers: 0,
  churned_customers_this_month: 0,
  sales_marketing_spend: 0,
  avg_revenue_per_account: 0,
  avg_price_per_unit: 0,
  avg_variable_cost_per_unit: 0,
  fixed_costs_monthly: 0,
  projected_annual_growth_rate: 0.2,
  discount_rate: 0.35,
  exit_multiple_revenue: 5,
  years_to_exit: 5,
  anticipated_roi: 10,
  investment_amount_requested: 0,
  industry_revenue_multiple: 6,
};

export function FinancialForm({
  initial,
  onSubmit,
  submitting,
}: {
  initial?: Record<string, number>;
  onSubmit: (values: Record<string, number>) => void;
  submitting?: boolean;
}) {
  const [values, setValues] = useState<Record<string, number>>({
    ...DEFAULTS,
    ...(initial || {}),
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(values);
      }}
    >
      <SectionLabel number="02" title="Financial Inputs" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {FIELDS.map((f) => (
          <Input
            key={f.key}
            label={f.label}
            type="number"
            step={f.step || "1"}
            value={values[f.key]}
            onChange={(e) =>
              setValues((v) => ({ ...v, [f.key]: parseFloat(e.target.value) || 0 }))
            }
          />
        ))}
      </div>
      <div className="mt-6">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save Financials & Recalculate"}
        </Button>
      </div>
    </form>
  );
}
