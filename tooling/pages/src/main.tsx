// 静态站入口：直接复用主应用的页面组件（默认导出已封装好日期处理）。
import { createRoot } from "react-dom/client";
import Home from "../../../app/page";
import "../../../app/globals.css";

createRoot(document.getElementById("root")!).render(<Home />);
