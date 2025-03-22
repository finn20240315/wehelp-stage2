document.addEventListener("DOMContentLoaded", async () => {
  const API_BASE_URL = "http://13.211.94.227:8000/api/attractions";
  const MRT_API_URL = "http://13.211.94.227:8000/api/mrts"; // 新增捷運站 API
  let allPlaces = []; // 存放所有景點資料
  let currentPage = 0; // 目前 API 請求的頁數
  let nextPage = 0; // 下一頁的頁碼
  let isLoading = false; // 避免重複請求
  let keyword = ""; // 存放搜尋關鍵字

  const searchInput = document.querySelector(".input"); // 取得輸入框
  const searchBtn = document.querySelector(".btn"); // 取得搜尋按鈕
  const attractionContainer = document.querySelector(".attractions-group"); // 景點顯示區
  const mrtList = document.querySelector(".container");
  const leftArrow = document.querySelector(".arrow-left");
  const rightArrow = document.querySelector(".arrow-right");

  console.log("searchBtn:", searchBtn);
  console.log("searchInput:", searchInput);

  // 初始化捷運站列表
  fetchMRTStations();

  // 左按鈕點擊事件 - 向左滾動
  leftArrow.addEventListener("click", () => {
    mrtList.scrollBy({ left: -150, behavior: "smooth" }); // 向左移動 150px
  });

  // 右按鈕點擊事件 - 向右滾動
  rightArrow.addEventListener("click", () => {
    mrtList.scrollBy({ left: 150, behavior: "smooth" }); // 向右移動 150px
  });

  // **搜尋按鈕點擊事件**
  searchBtn.addEventListener("click", () => {
    console.log("搜尋按鈕被點擊");
    startSearch();
  });

  // 監聽 Enter 鍵
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      console.log("按下 Enter 鍵");
      startSearch();
    }
  });

  // 取得 MRT 捷運站列表
  async function fetchMRTStations() {
    try {
      const response = await fetch(MRT_API_URL);
      if (!response.ok) throw new Error("API 回應錯誤");

      const data = await response.json();
      console.log("捷運站列表:", data);

      // 清空舊的捷運站列表
      mrtList.innerHTML = "";

      // 動態生成捷運站項目
      data.data.forEach((mrt) => {
        const li = document.createElement("li");
        li.className = "listitem";
        li.textContent = mrt;

        // 新增點擊事件，點擊後填入搜尋框並執行搜尋
        li.addEventListener("click", () => {
          searchInput.value = mrt; // 將捷運站名稱填入搜尋框
          startSearch(); // 重新搜尋
        });

        mrtList.appendChild(li);
      });
    } catch (error) {
      console.error("載入 MRT 站資料失敗:", error);
    }
  }

  function startSearch() {
    keyword = searchInput.value.trim();
    console.log("搜尋關鍵字:", keyword);

    currentPage = 0;
    nextPage = 0;
    allPlaces = [];
    attractionContainer.innerHTML = "";
    fetchPlaces(currentPage, true);
  }

  // **取得景點資料**
  async function fetchPlaces(page, isNewSearch = false) {
    if (isLoading || nextPage === null) return; // 若正在載入或沒有下一頁則不執行
    isLoading = true; // 設定載入中

    let url = `${API_BASE_URL}?page=${page}`;
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`;
    }
    console.log("發送 API 請求:", url);

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("API 回應錯誤");

      const data = await response.json();
      console.log("取得的資料:", data);

      if (isNewSearch) {
        attractionContainer.innerHTML = ""; // 若是新搜尋，清空列表
      }

      if (data && data.data.length > 0) {
        allPlaces = allPlaces.concat(data.data); // 合併新資料
        renderPlaces(data.data); // 只渲染新加載的資料
      } else {
        console.log("沒有符合條件的景點");
      }

      nextPage = data.nextPage; // 設定下一頁
    } catch (error) {
      console.error("載入資料失敗", error);
    } finally {
      isLoading = false; // 解除鎖定
    }
  }

  // **渲染景點**
  function renderPlaces(newData) {
    newData.forEach((place) => {
      attractionContainer.appendChild(createPlaceCard(place));
    });
  }

  // **建立景點卡片**
  function createPlaceCard(place) {
    const card = document.createElement("div");
    card.className = "attraction";

    const img = document.createElement("img");
    img.src = place.images.length > 0 ? place.images[0] : "";
    img.alt = place.name;

    const name = document.createElement("p");
    name.textContent = place.name;
    name.className = "name";

    const details = document.createElement("p");
    details.className = "details";

    const mrt = document.createElement("p");
    mrt.textContent = place.mrt || "無捷運站";
    mrt.className = "mrt";

    const category = document.createElement("p");
    category.textContent = place.category;
    category.className = "category";

    details.appendChild(mrt);
    details.appendChild(category);
    card.appendChild(img);
    card.appendChild(name);
    card.appendChild(details);

    return card;
  }

  // **偵測滾動到底部並載入更多資料**
  window.addEventListener("scroll", () => {
    const scrollTop = document.documentElement.scrollTop;
    const clientHeight = document.documentElement.clientHeight;
    const scrollHeight = document.documentElement.scrollHeight;

    // 顯示當前滾動狀態，便於除錯
    console.log("Scroll Top:", scrollTop);
    console.log("Client Height:", clientHeight);
    console.log("Scroll Height:", scrollHeight);

    if (scrollTop + clientHeight >= scrollHeight - 10) {
      console.log("接近底部，正在載入更多資料...");

      // 確保 nextPage 正確傳遞
      if (nextPage) {
        console.log("當前頁面:", nextPage);
        fetchPlaces(nextPage);
      } else {
        console.warn("nextPage 沒有設定，無法載入更多資料");
      }
    }
  });

  // 首次載入資料
  fetchPlaces(currentPage);
});
