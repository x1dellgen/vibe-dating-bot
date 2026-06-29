import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'https://0ffm52n9-8000.euw.devtunnels.ms/';

// ==================================================================
// 🎯 ВОТ ЭТОТ БЛОК МЫ АККУРАТНО ВСТАВЛЯЕМ МЕЖДУ API_URL И FUNCTION APP():
const tg = window.Telegram?.WebApp;
const tgUser = tg?.initDataUnsafe?.user;

// Автоматически подхватываем реальные данные из ТГ. 
// Если тестируешь просто в браузере, сработает заглушка справа (через ||)
const MY_TG_ID = tgUser?.id || 123456;
const MY_USERNAME = tgUser?.username || 'browser_test';
const MY_NAME = tgUser?.first_name || 'Тестовый Пользователь';

if (tg) {
  tg.ready();
  tg.expand(); // Разворачивает Mini App на весь экран телефона
}
// ==================================================================

function App() {
  const [appMode, setAppMode] = useState('portal'); // 'portal', 'dating'
  const [activeTab, setActiveTab] = useState('swipes'); // 'swipes', 'catalog', 'likes', 'matches', 'profile'
  const [editMode, setEditMode] = useState(false);
  
  // Данные профиля
  const [formData, setFormData] = useState({
    name: '', age: 18, city: '', gender: 'Парень', 
    preference: 'Девушек', description: '', search_scope: 'City', avatar_url: ''
  });

  // Состояния для вкладок знакоств
  const [catalogProfiles, setCatalogProfiles] = useState([]);
  const [currentCandidate, setCurrentCandidate] = useState(null);
  const [likedYouProfiles, setLikedYouProfiles] = useState([]);
  const [matches, setMatches] = useState([]);

  // Загрузка данных при смене вкладок
  useEffect(() => {
    if (appMode !== 'dating') return;

    if (activeTab === 'catalog') {
      fetchCatalog();
    } else if (activeTab === 'swipes') {
      fetchNextCandidate();
    } else if (activeTab === 'likes') {
      fetchLikedYou();
    } else if (activeTab === 'matches') {
      fetchMatches();
    }
  }, [activeTab, appMode]);

  // --- Запросы к API ---
  const fetchCatalog = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/catalog?current_user_id=${MY_TG_ID}`);
      setCatalogProfiles(res.data.profiles);
    } catch (err) { console.error("Ошибка каталога:", err); }
  };

  const fetchNextCandidate = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/match/next/${MY_TG_ID}`);
      setCurrentCandidate(res.data.candidate);
    } catch (err) { console.error("Ошибка получения кандидата:", err); }
  };

  const fetchLikedYou = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/interactions/liked-you/${MY_TG_ID}`);
      setLikedYouProfiles(res.data.profiles);
    } catch (err) { console.error("Ошибка загрузки лайков:", err); }
  };

  const fetchMatches = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/interactions/matches/${MY_TG_ID}`);
      setMatches(res.data.matches);
    } catch (err) { console.error("Ошибка загрузки мэтчей:", err); }
  };

  // Обработка свайпа (Лайк / Дизлайк)
  const handleAction = async (targetId, actionType) => {
    try {
      const res = await axios.post(`${API_URL}/api/match/action`, {
        user_id: MY_TG_ID,
        target_id: targetId,
        action: actionType
      });
      
      if (res.data.is_match) {
        alert("🎉 Взаимный мэтч! Отличный повод для общения!");
      }
      
      // Обновляем текущую вкладку
      if (activeTab === 'swipes') fetchNextCandidate();
      if (activeTab === 'likes') fetchLikedYou();
      if (activeTab === 'catalog') fetchCatalog();
    } catch (err) { alert("Ошибка действия: " + err.message); }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/register`, { 
        telegram_id: MY_TG_ID,
        username: 'test_user', 
        ...formData 
      });
      setEditMode(false);
      alert("Анкета сохранена! ✨");
    } catch (error) { alert("Ошибка сохранения: " + error.message); }
  };

 // --- 1. ЭКРАН ПОРТАЛА (Теперь зажат в рамки 500px по центру) ---
  if (appMode === 'portal') return (
    <div style={{ padding: '20px', maxWidth: '500px', margin: '0 auto', height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', fontFamily: 'sans-serif', boxSizing: 'border-box', backgroundColor: 'var(--tg-theme-bg-color, #121212)', color: 'var(--tg-theme-text-color, #ffffff)' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>🌌 Выберите режим приложения</h2>
      <button onClick={() => setAppMode('dating')} style={{ ...styles.mainButton, background: '#ff4757', marginBottom: '15px' }}>🔥 Дейтинг Сервис</button>
      <button onClick={() => alert('Анонимный чат в разработке!')} style={{ ...styles.mainButton, background: '#2ed573' }}>🎭 Анонимный Чат</button>
    </div>
  );

  // --- 2. ЭКРАН ДЕЙТИНГА ---
  return (
    <div style={{ padding: '20px', paddingBottom: '90px', fontFamily: 'sans-serif', maxWidth: '500px', margin: '0 auto', boxSizing: 'border-box', backgroundColor: 'var(--tg-theme-bg-color, #121212)', color: 'var(--tg-theme-text-color, #ffffff)', minHeight: '100vh' }}>
      
      {/* Шапка с кнопкой Назад */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <button onClick={() => setAppMode('portal')} style={{ background: 'var(--tg-theme-secondary-bg-color, #eee)', color: 'var(--tg-theme-text-color, #000000)', border: 'none', padding: '8px 12px', borderRadius: '8px', cursor: 'pointer' }}>⬅️ В портал</button>
        <h3 style={{ margin: 0 }}>🔥 VibeDating</h3>
      </div>

      {/* Контент вкладок */}
      <div style={{ marginTop: '20px' }}>
        
        {/* ВКЛАДКА: СВАЙПЫ */}
        {activeTab === 'swipes' && (
          <div>
            <h2 style={{ textAlign: 'center' }}>Поиск половинки</h2>
            {currentCandidate ? (
              <div style={styles.card}>
                <div style={styles.avatarPlaceholder}>📷 Нет фото</div>
                <h3>{currentCandidate.name}, {currentCandidate.age}</h3>
                <p>📍 {currentCandidate.city}</p>
                <p style={{ fontStyle: 'italic', color: '#555' }}>«{currentCandidate.description}»</p>
                
                <div style={{ display: 'flex', gap: '15px', marginTop: '20px' }}>
                  <button onClick={() => handleAction(currentCandidate.telegram_id, 'dislike')} style={{ ...styles.mainButton, background: '#ccc' }}>❌ Пропустить</button>
                  <button onClick={() => handleAction(currentCandidate.telegram_id, 'like')} style={{ ...styles.mainButton, background: '#ff4757' }}>❤️ Лайк</button>
                </div>
              </div>
            ) : (
              <p style={{ textAlign: 'center', color: '#777', marginTop: '40px' }}>Анкеты пока закончились! Загляни в каталог или подожди новых пользователей. 💤</p>
            )}
          </div>
        )}

        {/* ВКЛАДКА: КАТАЛОГ */}
        {activeTab === 'catalog' && (
          <div>
            <h2>🗂️ Каталог анкет</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {catalogProfiles.map(p => (
                <div key={p.telegram_id} style={{ ...styles.card, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ flex: 1, paddingRight: '10px' }}>
                    <h4 style={{ margin: '0 0 5px 0' }}>{p.name}, {p.age}</h4>
                    <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>📍 {p.city}</p>
                    <p style={{ margin: '5px 0 0 0', fontSize: '13px', color: '#444' }}>{p.description}</p>
                  </div>
                  <button onClick={() => handleAction(p.telegram_id, 'like')} style={{ background: '#ffebee', border: 'none', borderRadius: '50%', width: '45px', height: '45px', fontSize: '20px', cursor: 'pointer', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>❤️</button>
                </div>
              ))}
              {catalogProfiles.length === 0 && <p style={{ textAlign: 'center', color: '#777' }}>Каталог пуст.</p>}
            </div>
          </div>
        )}

        {/* ВКЛАДКА: ЛАЙКИ */}
        {activeTab === 'likes' && (
          <div>
            <h2>⭐ Вы понравились</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {likedYouProfiles.map(p => (
                <div key={p.telegram_id} style={{ ...styles.card, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: '5px solid #ff4757' }}>
                  <div style={{ flex: 1, paddingRight: '10px' }}>
                    <h4 style={{ margin: '0 0 5px 0' }}>{p.name}, {p.age}</h4>
                    <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>📍 {p.city}</p>
                    <p style={{ margin: '5px 0 0 0', fontSize: '13px' }}>{p.description}</p>
                  </div>
                  <button onClick={() => handleAction(p.telegram_id, 'like')} style={{ ...styles.mainButton, width: 'auto', background: '#2ed573', padding: '8px 12px', fontSize: '14px', flexShrink: 0 }}>❤️ В ответ</button>
                </div>
              ))}
              {likedYouProfiles.length === 0 && (
                <p style={{ textAlign: 'center', color: '#777', marginTop: '40px' }}>Пока никто не поставил вам лайк. Попробуйте проявить активность в Свайпах! 😉</p>
              )}
            </div>
          </div>
        )}

        {/* ВКЛАДКА: МЭТЧИ */}
        {activeTab === 'matches' && (
          <div>
            <h2>💬 Взаимные симпатии</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {matches.map(p => (
                <div key={p.telegram_id} style={styles.card}>
                  <h4>🎉 {p.name}, {p.age}</h4>
                  <p style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#666' }}>Телеграм для связи: <b>@{p.username}</b></p>
                  <button onClick={() => alert(`Открываем чат с @${p.username}`)} style={{ ...styles.mainButton, background: '#54a0ff' }}>💬 Написать сообщение</button>
                </div>
              ))}
              {matches.length === 0 && <p style={{ textAlign: 'center', color: '#777', marginTop: '40px' }}>Взаимных мэтчей пока нет. Всё впереди! 😉</p>}
            </div>
          </div>
        )}

{/* ВКЛАДКА: ПРОФИЛЬ */}
{activeTab === 'profile' && (
  <div style={{ color: 'var(--tg-theme-text-color, #000)' }}>
    <h2>👤 Ваш профиль</h2>
    {editMode ? (
      <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <input type="text" placeholder="Имя" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required style={styles.input} />
        <input type="number" placeholder="Возраст" value={formData.age} onChange={e => setFormData({...formData, age: parseInt(e.target.value)})} required style={styles.input} />
        <input type="text" placeholder="Город" value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})} required style={styles.input} />
        <select value={formData.gender} onChange={e => setFormData({...formData, gender: e.target.value})} style={styles.input}>
          <option value="Парень">Парень</option>
          <option value="Девушка">Девушка</option>
        </select>
        <select value={formData.preference} onChange={e => setFormData({...formData, preference: e.target.value})} style={styles.input}>
          <option value="Девушек">Ищу Девушек</option>
          <option value="Парней">Ищу Парней</option>
          <option value="Всех">Ищу Всех</option>
        </select>
        <textarea placeholder="О себе" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} style={styles.input} />
        <button type="submit" style={styles.mainButton}>💾 Сохранить изменения</button>
        <button type="button" onClick={() => setEditMode(false)} style={{ ...styles.mainButton, backgroundColor: 'var(--tg-theme-secondary-bg-color, #ccc)', color: 'var(--tg-theme-text-color, #000)' }}>❌ Отмена</button>
      </form>
    ) : (
<div style={{
  padding: '20px',
  borderRadius: '16px',
  marginBottom: '20px',
  /* Вот тут принудительно перекрываем цвета */
  backgroundColor: 'var(--tg-theme-secondary-bg-color, #ffffff)', 
  color: 'var(--tg-theme-text-color, #000000)',
  border: '1px solid var(--tg-theme-hint-color, #ccc)'
}}>
  <h3 style={{ color: 'var(--tg-theme-text-color, #000000)', marginTop: '0' }}>
    {formData.name || "Анкета не заполнена"}, {formData.age}
  </h3>
  <p style={{ color: 'var(--tg-theme-text-color, #000000)' }}>📍 {formData.city || "Город не указан"}</p>
  <p style={{ color: 'var(--tg-theme-text-color, #000000)' }}>📋 {formData.description || "Описание отсутствует"}</p>
  
  <button 
    onClick={() => setEditMode(true)} 
    style={{
      width: '100%',
      padding: '12px',
      border: 'none',
      borderRadius: '12px',
      cursor: 'pointer',
      /* Адаптивная кнопка */
      backgroundColor: 'var(--tg-theme-button-color, #ff4757)',
      color: 'var(--tg-theme-button-text-color, #ffffff)',
      fontWeight: 'bold'
    }}
  >
    ✏️ Редактировать
  </button>
</div>
    )}
  </div>
)}
      </div>

      {/* Навигационная панель (Теперь центрируется и не растягивается) */}
      <div style={styles.navBar}>
        <button onClick={() => setActiveTab('swipes')} style={{...styles.tab, background: activeTab === 'swipes' ? '#fff' : 'transparent'}}>🔥</button>
        <button onClick={() => setActiveTab('catalog')} style={{...styles.tab, background: activeTab === 'catalog' ? '#fff' : 'transparent'}}>🗂️</button>
        <button onClick={() => setActiveTab('likes')} style={{...styles.tab, background: activeTab === 'likes' ? '#fff' : 'transparent'}}>⭐</button>
        <button onClick={() => setActiveTab('matches')} style={{...styles.tab, background: activeTab === 'matches' ? '#fff' : 'transparent'}}>💬</button>
        <button onClick={() => setActiveTab('profile')} style={{...styles.tab, background: activeTab === 'profile' ? '#fff' : 'transparent'}}>👤</button>
      </div>
    </div>
  );
}

const styles = {
  input: { width: '100%', padding: '10px', boxSizing: 'border-box', borderRadius: '8px', border: '1px solid #ccc' },
  mainButton: { width: '100%', padding: '12px', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' },
  card: { padding: '20px', border: '1px solid #eee', borderRadius: '15px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', background: '#fff', boxSizing: 'border-box' },
  avatarPlaceholder: { width: '100%', height: '200px', background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#aaa', borderRadius: '10px', marginBottom: '15px' },
  
  // Магия фиксации нижнего бара по центру экрана
  navBar: { 
    position: 'fixed', 
    bottom: 0, 
    left: '50%', 
    transform: 'translateX(-50%)', 
    width: '100%', 
    maxWidth: '500px', 
    height: '65px', 
    background: '#f8f9fa', 
    display: 'flex', 
    justifyContent: 'space-around', 
    alignItems: 'center', 
    borderTop: '1px solid #ddd', 
    boxShadow: '0 -2px 10px rgba(0,0,0,0.05)',
    boxSizing: 'border-box',
    padding: '0 10px',
    zIndex: 1000
  },
  tab: { border: 'none', fontSize: '22px', cursor: 'pointer', width: '50px', height: '45px', borderRadius: '10px', transition: '0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center' }
};

export default App;