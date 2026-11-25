"use client";

import React, { useState } from "react";
import styles from "../styles/Reservation.module.css";

export interface EquipmentSelection {
  name: string;
  quantity: number;
  serial_or_notes?: string;
  selected: boolean;
}

interface EquipmentSelectorProps {
  items: EquipmentSelection[];
  onChange: (items: EquipmentSelection[]) => void;
}

export default function EquipmentSelector({ items, onChange }: EquipmentSelectorProps) {
  const [customItemName, setCustomItemName] = useState("");
  const [showAddCustom, setShowAddCustom] = useState(false);

  const toggleSelect = (index: number) => {
    const updated = [...items];
    updated[index].selected = !updated[index].selected;
    onChange(updated);
  };

  const updateQuantity = (index: number, delta: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = [...items];
    const newQty = Math.max(1, updated[index].quantity + delta);
    updated[index].quantity = newQty;
    if (!updated[index].selected) {
      updated[index].selected = true;
    }
    onChange(updated);
  };

  const handleAddCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customItemName.trim()) return;

    const newItem: EquipmentSelection = {
      name: customItemName.trim(),
      quantity: 1,
      selected: true,
    };
    onChange([...items, newItem]);
    setCustomItemName("");
    setShowAddCustom(false);
  };

  return (
    <div>
      <div className={styles.equipmentGrid}>
        {items.map((item, index) => {
          const isSelected = item.selected;
          return (
            <div
              key={`${item.name}-${index}`}
              className={`${styles.equipmentCard} ${
                isSelected ? styles.equipmentCardSelected : ""
              }`}
              onClick={() => toggleSelect(index)}
            >
              <div className={styles.equipmentHeader}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSelect(index)}
                  className={styles.checkbox}
                  onClick={(e) => e.stopPropagation()}
                />
                <span className={styles.equipmentName}>{item.name}</span>
              </div>

              {isSelected && (
                <div
                  className={styles.quantityRow}
                  onClick={(e) => e.stopPropagation()}
                >
                  <span>Cantidad:</span>
                  <div className={styles.quantityControls}>
                    <button
                      type="button"
                      className={styles.qtyBtn}
                      onClick={(e) => updateQuantity(index, -1, e)}
                      disabled={item.quantity <= 1}
                    >
                      -
                    </button>
                    <span className={styles.qtyDisplay}>{item.quantity}</span>
                    <button
                      type="button"
                      className={styles.qtyBtn}
                      onClick={(e) => updateQuantity(index, 1, e)}
                    >
                      +
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: "12px", marginBottom: "20px" }}>
        {!showAddCustom ? (
          <button
            type="button"
            onClick={() => setShowAddCustom(true)}
            style={{
              background: "transparent",
              border: "1px dashed var(--border-accent)",
              color: "var(--accent-cyan)",
              padding: "8px 16px",
              borderRadius: "var(--radius-sm)",
              fontSize: "13px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            + Agregar accesorio o equipo personalizado
          </button>
        ) : (
          <div style={{ display: "flex", gap: "8px", maxWidth: "420px" }}>
            <input
              type="text"
              placeholder="Ej. Batería externa Anker, Facial Interface de repuesto..."
              value={customItemName}
              onChange={(e) => setCustomItemName(e.target.value)}
              className={styles.input}
              style={{ fontSize: "13px", padding: "8px 12px" }}
              autoFocus
            />
            <button
              type="button"
              onClick={handleAddCustom}
              style={{
                background: "var(--accent-blue)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-sm)",
                padding: "0 14px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              Agregar
            </button>
            <button
              type="button"
              onClick={() => setShowAddCustom(false)}
              style={{
                background: "transparent",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-secondary)",
                borderRadius: "var(--radius-sm)",
                padding: "0 10px",
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
