import { useEffect, useState } from 'react'
import WebApp from '@twa-dev/sdk'
const tg = WebApp.ready ? WebApp : WebApp.default;
function App() {
  const [user, setUser] = useState(null)
  
  // Состояния для полей формы
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [city, setCity] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  useEffect(() => {
    tg.ready()
    // Проверяем, запущены ли мы внутри Telegram
    if (tg.initDataUnsafe?.user) {
      setUser(tg.initDataUnsafe.user)
      // Сразу подставим имя из телеграма как дефолтное
      setName(tg.initDataUnsafe.user.first_name || '')
    } else {
      // Локальный фейковый юзер для тестов в обычном браузере
      setUser({ id: 12345678, first_name: 'Иван' })
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Собираем данные для отправки
    const profileData = {
      telegram_id: user.id,
      name: name,
      age: parseInt(age) || 0,
      city: city
    }

    try {
      // Отправляем POST-запрос на наш FastAPI бэкенд
      const response = await fetch('http://127.0.0.1:8000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      })

      const result = await response.json()
      
      if (result.success) {
        setStatusMessage('✅ ' + result.message)
      } else {
        setStatusMessage('❌ Что-то пошло не так')
      }
    } catch (error) {
      console.error(error)
      setStatusMessage('❌ Ошибка соединения с сервером')
    }
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '400px', margin: '0 auto' }}>
      <h2 style={{ textAlign: 'center' }}>Создание анкеты</h2>
      
      <p style={{ textAlign: 'center', color: '#666' }}>
        Привет, {user?.first_name}! Твой ID: {user?.id}
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          Имя:
          <input 
            type="text" 
            value={name} 
            onChange={(e) => setName(e.target.value)} 
            required 
            style={{ padding: '8px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          Возраст:
          <input 
            type="number" 
            value={age} 
            onChange={(e) => setAge(e.target.value)} 
            required 
            style={{ padding: '8px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          Город:
          <input 
            type="text" 
            value={city} 
            onChange={(e) => setCity(e.target.value)} 
            required 
            style={{ padding: '8px', borderRadius: '5px', border: '1px solid #ccc' }}
          />
        </label>

        <button 
          type="submit" 
          style={{ 
            padding: '10px', 
            background: '#0088cc', 
            color: 'white', 
            border: 'none', 
            borderRadius: '5px', 
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Сохранить анкету
        </button>
      </form>

      {statusMessage && (
        <p style={{ textAlign: 'center', marginTop: '20px', fontWeight: 'bold' }}>
          {statusMessage}
        </p>
      )}
    </div>
  )
}

export default App