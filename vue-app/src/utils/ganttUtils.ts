import { gantt } from 'dhtmlx-gantt'

export const setGanttScale = (mode: string) => {
  if (mode === "hour") {
    gantt.config.scale_unit = "day";
    gantt.config.date_scale = "%Y-%m-%d";
    gantt.config.subscales = [{ unit: "hour", step: 1, date: "%H:%i" }];
  } else if (mode === "day") {
    gantt.config.scale_unit = "week";
    gantt.config.date_scale = "第 %W 週";
    gantt.config.subscales = [{ unit: "day", step: 1, date: "%m/%d" }];
  } else if (mode === "week") {
    gantt.config.scale_unit = "month";
    gantt.config.date_scale = "%Y-%m";
    gantt.config.subscales = [{ unit: "week", step: 1, date: "第 %W 週" }];
  } else if (mode === "month") {
    gantt.config.scale_unit = "year";
    gantt.config.date_scale = "%Y";
    gantt.config.subscales = [{ unit: "month", step: 1, date: "%m月" }];
  }
  gantt.config.scale_height = 60;
  gantt.render();
}

export const parseDate = (dateStr: string): Date => {
  return new Date(dateStr);
}

export const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '';
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const mm = String(date.getMinutes()).padStart(2, '0');
  return `${y}-${m}-${d} ${hh}:${mm}`;
}

export const generateColorPool = (): string[] => {
  return [
    "#FF9999", "#99CCFF", "#99FF99", "#FFCC99", "#CC99FF", "#FFB6C1", "#FFD700",
    "#7FFFD4", "#FF69B4", "#20B2AA", "#87CEFA", "#32CD32", "#FFA07A", "#9370DB",
    "#40E0D0", "#FF6347", "#8FBC8F", "#6495ED", "#F08080", "#48D1CC", "#BA55D3",
    "#BDB76B", "#00CED1", "#FF4500", "#228B22", "#8B0000"
  ];
}
