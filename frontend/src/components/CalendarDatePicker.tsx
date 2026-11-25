"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import styles from "../styles/CalendarDatePicker.module.css";

interface CalendarDatePickerProps {
  value: string; // ISO date string: YYYY-MM-DD
  onChange: (date: string) => void;
  minDate?: string;
  id?: string;
}

const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

const WEEK_DAYS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

export default function CalendarDatePicker({
  value,
  onChange,
  minDate,
  id,
}: CalendarDatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Parse current selected date
  const parsedDate = useMemo(() => {
    if (!value) return new Date();
    const parts = value.split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }, [value]);

  const [currentYear, setCurrentYear] = useState(parsedDate.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(parsedDate.getMonth());

  // Close calendar when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Update current year/month when value changes externally
  const [prevValue, setPrevValue] = useState(value);
  if (value !== prevValue) {
    setPrevValue(value);
    if (value) {
      const parts = value.split("-").map(Number);
      setCurrentYear(parts[0]);
      setCurrentMonth(parts[1] - 1);
    }
  }

  const prevMonth = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
  };

  const nextMonth = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
  };

  // Days in month
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfWeek = (new Date(currentYear, currentMonth, 1).getDay() + 6) % 7; // Monday = 0

  const handleSelectDay = (day: number) => {
    const formattedMonth = String(currentMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    const newDateStr = `${currentYear}-${formattedMonth}-${formattedDay}`;
    onChange(newDateStr);
    setIsOpen(false);
  };

  // Quick preset helper
  const setQuickDate = (offsetDays: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    onChange(`${y}-${m}-${day}`);
    setIsOpen(false);
  };

  // Formatted display text
  const displayFormatted = useMemo(() => {
    if (!value) return "Seleccionar fecha...";
    try {
      const parts = value.split("-").map(Number);
      const d = new Date(parts[0], parts[1] - 1, parts[2]);
      const formatter = new Intl.DateTimeFormat("es-CL", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
      });
      return formatter.format(d);
    } catch {
      return value;
    }
  }, [value]);

  const todayStr = useMemo(() => {
    const t = new Date();
    return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
  }, []);

  return (
    <div className={styles.datePickerWrapper} ref={containerRef}>
      <button
        id={id}
        type="button"
        className={styles.inputButton}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Abrir selector de fecha con calendario"
      >
        <span>{displayFormatted}</span>
        <span className={styles.calendarIcon}>📅</span>
      </button>

      {isOpen && (
        <div className={styles.popup}>
          {/* Header Month / Year */}
          <div className={styles.calendarHeader}>
            <button
              type="button"
              className={styles.navBtn}
              onClick={prevMonth}
              title="Mes anterior"
            >
              ←
            </button>
            <span className={styles.monthTitle}>
              {MONTH_NAMES[currentMonth]} {currentYear}
            </span>
            <button
              type="button"
              className={styles.navBtn}
              onClick={nextMonth}
              title="Mes siguiente"
            >
              →
            </button>
          </div>

          {/* Quick buttons */}
          <div className={styles.quickRow}>
            <button
              type="button"
              className={styles.quickBtn}
              onClick={(e) => setQuickDate(0, e)}
            >
              Hoy
            </button>
            <button
              type="button"
              className={styles.quickBtn}
              onClick={(e) => setQuickDate(1, e)}
            >
              Mañana
            </button>
            <button
              type="button"
              className={styles.quickBtn}
              onClick={(e) => setQuickDate(7, e)}
            >
              +1 Semana
            </button>
          </div>

          {/* Week Days */}
          <div className={styles.weekDaysRow}>
            {WEEK_DAYS.map((w) => (
              <span key={w} className={styles.weekDay}>
                {w}
              </span>
            ))}
          </div>

          {/* Days Grid */}
          <div className={styles.daysGrid}>
            {/* Empty padding cells for first day of week */}
            {Array.from({ length: firstDayOfWeek }).map((_, idx) => (
              <span key={`empty-${idx}`} className={styles.emptyCell} />
            ))}

            {/* Days of month */}
            {Array.from({ length: daysInMonth }).map((_, idx) => {
              const dayNum = idx + 1;
              const formattedM = String(currentMonth + 1).padStart(2, "0");
              const formattedD = String(dayNum).padStart(2, "0");
              const cellDateStr = `${currentYear}-${formattedM}-${formattedD}`;

              const isSelected = cellDateStr === value;
              const isToday = cellDateStr === todayStr;
              const isDisabled = minDate ? cellDateStr < minDate : false;

              let cellClass = styles.dayCell;
              if (isSelected) cellClass += ` ${styles.selectedDay}`;
              if (isToday && !isSelected) cellClass += ` ${styles.todayCell}`;
              if (isDisabled) cellClass += ` ${styles.disabledDay}`;

              return (
                <button
                  key={dayNum}
                  type="button"
                  disabled={isDisabled}
                  className={cellClass}
                  onClick={() => handleSelectDay(dayNum)}
                >
                  {dayNum}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
