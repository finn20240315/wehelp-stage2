document.addEventListener("DOMContentLoaded", () => {
  const API_BASE_URL = "http://127.0.0.1:8000/api/attractions";
  let allPlaces = []; // 存放所有景點資料
  let currentPage = 0; // 目前 API 請求的頁數
  let nextPage = 0; // 下一頁的頁碼
  let isLoading = false; // 避免重複請求

  // **取得景點資料**
  async function fetchPlaces(page) {
    if (isLoading || nextPage === null) return; // 若正在載入或沒有下一頁則不執行

    isLoading = true; // 設定載入中
    try {
      const response = await fetch(`${API_BASE_URL}?page=${page}`);
      const data = await response.json();

      if (data && data.data.length > 0) {
        allPlaces = allPlaces.concat(data.data); // 合併新資料
        renderPlaces(data.data); // 只渲染新加載的資料
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
    const container = document.querySelector(".attractions-group");
    newData.forEach((place) => {
      container.appendChild(createPlaceCard(place));
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
    mrt.textContent = place.mrt;
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
  function handleScroll() {
    if (
      document.documentElement.scrollTop ||
      document.body.scrollTop + document.documentElement.clientHeight >=
        document.documentElement.scrollHeight - 10
    ) {
      fetchPlaces(nextPage); // 讀取下一頁
    }
  }

  // **初始化**
  window.addEventListener("scroll", handleScroll);
  fetchPlaces(currentPage); // 先加載第一頁
});
