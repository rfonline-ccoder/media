import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Separator } from "./components/ui/separator";
import { 
  Home, 
  User, 
  ShoppingCart, 
  FileText, 
  Shield, 
  LogIn, 
  UserPlus, 
  Coins, 
  AlertTriangle,
  Settings,
  TrendingUp,
  Users,
  Activity
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext(null);

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = (newToken, userData) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    setIsLoading(false);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setIsLoading(false);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user && !!token, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <nav className="bg-gradient-to-r from-blue-900 to-purple-900 text-white p-4 shadow-lg">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Activity className="h-8 w-8" />
          <h1 className="text-2xl font-bold">SwagMedia</h1>
        </div>
        
        <div className="flex items-center space-x-6">
          <a href="/" className="hover:text-blue-200 flex items-center space-x-1">
            <Home className="h-4 w-4" />
            <span>Главная</span>
          </a>
          
          <a href="/media-list" className="hover:text-blue-200 flex items-center space-x-1">
            <Users className="h-4 w-4" />
            <span>Медиа</span>
          </a>

          {isAuthenticated && (
            <>
              <a href="/profile" className="hover:text-blue-200 flex items-center space-x-1">
                <User className="h-4 w-4" />
                <span>Профиль</span>
              </a>
              
              <a href="/shop" className="hover:text-blue-200 flex items-center space-x-1">
                <ShoppingCart className="h-4 w-4" />
                <span>Магазин</span>
              </a>
              
              <a href="/reports" className="hover:text-blue-200 flex items-center space-x-1">
                <FileText className="h-4 w-4" />
                <span>Отчеты</span>
              </a>

              {user?.admin_level >= 1 && (
                <a href="/admin" className="hover:text-blue-200 flex items-center space-x-1">
                  <Shield className="h-4 w-4" />
                  <span>Админ</span>
                </a>
              )}

              <div className="flex items-center space-x-2">
                <Coins className="h-4 w-4 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">{user?.balance || 0} MC</span>
              </div>

              <Button variant="ghost" size="sm" onClick={logout}>
                Выйти
              </Button>
            </>
          )}

          {!isAuthenticated && (
            <div className="flex space-x-2">
              <Button variant="ghost" size="sm" asChild>
                <a href="/login">Войти</a>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a href="/register">Регистрация</a>
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

// Home Page
const HomePage = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 mb-6 animate-pulse">
            Добро пожаловать в SwagMedia
          </h1>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
            🎯 Платформа для медиа-создателей с собственной экономикой и системой вознаграждений
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-blue-600 font-semibold">💎 Медиа-коины</span>
            </div>
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-purple-600 font-semibold">🚀 Премиум контент</span>
            </div>
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-pink-600 font-semibold">⭐ Эксклюзивные товары</span>
            </div>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-blue-700">
                  <Users className="h-8 w-8" />
                  <span className="text-lg">Медиа участников</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-blue-600 mb-2">{stats.total_media}</div>
                <p className="text-blue-600/80">Активных создателей контента</p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-green-700">
                  <TrendingUp className="h-8 w-8" />
                  <span className="text-lg">Потрачено MC</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-green-600 mb-2">{stats.total_mc_spent.toLocaleString()}</div>
                <p className="text-green-600/80">Медиа-коинов в магазине</p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-yellow-700">
                  <Coins className="h-8 w-8" />
                  <span className="text-lg">Активных MC</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-yellow-600 mb-2">{stats.total_mc_current.toLocaleString()}</div>
                <p className="text-yellow-600/80">В обращении сейчас</p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">
            Начните свой путь в мире медиа
          </h2>
          <div className="space-x-4">
            <Button size="lg" asChild>
              <a href="/register">Подать заявку</a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="/media-list">Посмотреть медиа</a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Registration Page
const RegisterPage = () => {
  const [formData, setFormData] = useState({
    nickname: '',
    login: '',
    password: '',
    vk_link: '',
    channel_link: ''
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/register`, formData);
      setMessage('Заявка на регистрацию подана! Ожидайте одобрения администратора.');
      setFormData({ nickname: '', login: '', password: '', vk_link: '', channel_link: '' });
    } catch (error) {
      setMessage(`Ошибка: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Регистрация</CardTitle>
          <CardDescription>Подайте заявку на участие в SwagMedia</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="nickname">Никнейм</Label>
              <Input
                id="nickname"
                value={formData.nickname}
                onChange={(e) => setFormData({...formData, nickname: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({...formData, login: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="vk_link">Ссылка на VK</Label>
              <Input
                id="vk_link"
                value={formData.vk_link}
                onChange={(e) => setFormData({...formData, vk_link: e.target.value})}
                placeholder="https://vk.com/username"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="channel_link">Ссылка на канал</Label>
              <Input
                id="channel_link"
                value={formData.channel_link}
                onChange={(e) => setFormData({...formData, channel_link: e.target.value})}
                placeholder="https://t.me/channel или https://youtube.com/channel"
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Подача заявки...' : 'Подать заявку'}
            </Button>
          </form>

          {message && (
            <Alert className="mt-4">
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({ login: '', password: '' });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/login`, formData);
      login(response.data.access_token, response.data.user);
      // Force page reload to ensure proper navigation
      setTimeout(() => {
        window.location.href = '/';
      }, 100);
    } catch (error) {
      setMessage(`Ошибка: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Авторизация</CardTitle>
          <CardDescription>Войдите в свой аккаунт</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({...formData, login: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Вход...' : 'Войти'}
            </Button>
          </form>

          {message && (
            <Alert className="mt-4" variant={message.includes('Ошибка') ? 'destructive' : 'default'}>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}

          <div className="mt-4 text-center">
            <Button variant="link" asChild>
              <a href="/register">Нет аккаунта? Подать заявку</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Media List Page
const MediaListPage = () => {
  const [mediaList, setMediaList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMediaList();
  }, []);

  const fetchMediaList = async () => {
    try {
      const response = await axios.get(`${API}/media-list`);
      setMediaList(response.data);
    } catch (error) {
      console.error('Failed to fetch media list:', error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Список медиа</h1>
        
        {loading ? (
          <div className="text-center">Загрузка...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mediaList.map((media, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    {media.nickname}
                    <Badge variant={media.media_type === 'Платное' ? 'default' : 'secondary'}>
                      {media.media_type}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div>
                      <strong>Канал:</strong>{' '}
                      <a 
                        href={media.channel_link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        Перейти
                      </a>
                    </div>
                    <div>
                      <strong>VK:</strong>{' '}
                      <a 
                        href={media.vk_link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        Профиль
                      </a>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Profile Page
const ProfilePage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [reports, setReports] = useState([]);

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      fetchReports();
    }
  }, [isAuthenticated, isLoading]);

  const fetchReports = async () => {
    try {
      const response = await axios.get(`${API}/reports/my`);
      setReports(response.data);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl">Профиль: {user.nickname}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Основная информация</h3>
                <div className="space-y-2">
                  <div><strong>Канал:</strong> <a href={user.channel_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Перейти</a></div>
                  <div><strong>VK:</strong> <a href={user.vk_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Профиль</a></div>
                  <div>
                    <strong>Тип медиа:</strong>{' '}
                    <Badge variant={user.media_type === 1 ? 'default' : 'secondary'}>
                      {user.media_type === 1 ? 'Платное' : 'Бесплатное'}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Статистика</h3>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Coins className="h-4 w-4 text-yellow-600" />
                    <span><strong>Медиа-коины:</strong> {user.balance} MC</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <span><strong>Предупреждения:</strong> {user.warnings || 0}/3</span>
                  </div>
                  <div><strong>Отчетов подано:</strong> {reports.length}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>История отчетов</CardTitle>
          </CardHeader>
          <CardContent>
            {reports.length === 0 ? (
              <div className="text-center text-gray-500">Отчетов пока нет</div>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                  <div key={report.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm text-gray-500">
                        {new Date(report.created_at).toLocaleString('ru-RU')}
                      </div>
                      <Badge variant={
                        report.status === 'approved' ? 'default' :
                        report.status === 'rejected' ? 'destructive' : 'secondary'
                      }>
                        {report.status === 'approved' ? 'Одобрен' :
                         report.status === 'rejected' ? 'Отклонен' : 'На рассмотрении'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      {report.links.map((link, index) => (
                        <div key={index} className="flex justify-between items-center">
                          <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {link.url}
                          </a>
                          <span className="text-sm text-gray-600">{link.views} просмотров</span>
                        </div>
                      ))}
                    </div>
                    {report.admin_comment && (
                      <div className="mt-2 text-sm text-gray-600">
                        <strong>Комментарий:</strong> {report.admin_comment}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Shop Page
const ShopPage = () => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchShopItems();
  }, []);

  const fetchShopItems = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/shop/items`);
      console.log('Shop items response:', response.data);
      const itemsData = response.data || [];
      setItems(itemsData);
      
      if (itemsData.length > 0) {
        const uniqueCategories = [...new Set(itemsData.map(item => item.category))];
        console.log('Categories found:', uniqueCategories);
        setCategories(uniqueCategories);
        setMessage(''); // Clear any previous error messages
      } else {
        setMessage('Товары не найдены. Пожалуйста, обратитесь к администратору.');
      }
    } catch (error) {
      console.error('Failed to fetch shop items:', error);
      setMessage('Ошибка загрузки товаров. Попробуйте обновить страницу.');
    }
    setLoading(false);
  };

  const handlePurchase = async (itemId) => {
    if (!isAuthenticated) {
      setMessage('Войдите в аккаунт для покупок');
      return;
    }

    try {
      await axios.post(`${API}/shop/purchase`, { item_id: itemId });
      setMessage('Заявка на покупку подана! Ожидайте одобрения администратора.');
    } catch (error) {
      setMessage(`Ошибка: ${error.response?.data?.detail || error.message}`);
    }
  };

  const filteredItems = selectedCategory === 'all' 
    ? items 
    : items.filter(item => item.category === selectedCategory);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Магазин SwagMedia
          </h1>
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="bg-white rounded-lg shadow-lg px-6 py-3 flex items-center space-x-3">
              <Coins className="h-8 w-8 text-yellow-600" />
              <div>
                <div className="text-sm text-gray-500">Ваш баланс</div>
                <div className="text-2xl font-bold text-gray-900">{user?.balance?.toLocaleString() || 0} MC</div>
              </div>
            </div>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Приобретайте эксклюзивные товары и услуги за медиа-коины. Зарабатывайте MC подавая отчеты!
          </p>
        </div>

        {message && (
          <Alert className="mb-6">
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}

        {categories.length > 0 && (
          <div className="mb-8">
            <div className="flex flex-wrap justify-center gap-3 mb-4">
              <Button
                variant={selectedCategory === 'all' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('all')}
                className="transition-all duration-200"
              >
                Все категории ({items.length})
              </Button>
              {categories.map(category => {
                const categoryCount = items.filter(item => item.category === category).length;
                return (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    onClick={() => setSelectedCategory(category)}
                    className="transition-all duration-200"
                  >
                    {category} ({categoryCount})
                  </Button>
                );
              })}
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center">Загрузка товаров...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => (
              <Card key={item.id} className="hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg font-semibold text-gray-800 leading-tight">
                      {item.name}
                    </CardTitle>
                    <Badge 
                      variant={item.category === 'Премиум' ? 'default' : 
                              item.category === 'Буст' ? 'secondary' : 'outline'}
                      className="ml-2 flex-shrink-0"
                    >
                      {item.category}
                    </Badge>
                  </div>
                  <CardDescription className="text-sm text-gray-600 mt-2">
                    {item.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <Coins className="h-5 w-5 text-yellow-600" />
                      <span className="text-xl font-bold text-gray-900">{item.price} MC</span>
                    </div>
                    <Button 
                      onClick={() => handlePurchase(item.id)}
                      disabled={user?.balance < item.price}
                      className={user?.balance < item.price ? 
                        "bg-gray-400 cursor-not-allowed" : 
                        "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"}
                    >
                      {user?.balance < item.price ? 'Недостаточно MC' : 'Купить'}
                    </Button>
                  </div>
                  
                  {/* Progress bar showing affordability */}
                  {user && (
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Ваш баланс: {user.balance} MC</span>
                        <span>{user.balance >= item.price ? '✅ Доступно' : '❌ Нужно больше MC'}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            user.balance >= item.price 
                              ? 'bg-gradient-to-r from-green-400 to-green-600' 
                              : 'bg-gradient-to-r from-red-400 to-orange-500'
                          }`}
                          style={{ width: `${Math.min(100, (user.balance / item.price) * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && filteredItems.length === 0 && items.length > 0 && (
          <div className="text-center text-gray-500">
            Нет товаров в категории "{selectedCategory}"
          </div>
        )}
        
        {!loading && items.length === 0 && (
          <div className="text-center text-gray-500">
            Товары загружаются... Если товары не появились, обновите страницу.
          </div>
        )}
        
        {!loading && filteredItems.length > 0 && (
          <div className="mb-4 text-center">
            <p className="text-gray-600">Найдено товаров: {filteredItems.length} из {items.length}</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Reports Page
const ReportsPage = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [links, setLinks] = useState([{ url: '', views: 0 }]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/reports`, { links: links.filter(link => link.url) });
      setMessage('Отчет успешно подан!');
      setLinks([{ url: '', views: 0 }]);
    } catch (error) {
      setMessage(`Ошибка: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  const addLink = () => {
    setLinks([...links, { url: '', views: 0 }]);
  };

  const removeLink = (index) => {
    setLinks(links.filter((_, i) => i !== index));
  };

  const updateLink = (index, field, value) => {
    const newLinks = [...links];
    newLinks[index][field] = field === 'views' ? parseInt(value) || 0 : value;
    setLinks(newLinks);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Подача отчета</CardTitle>
            <CardDescription>Добавьте ссылки на ваши видео и укажите количество просмотров</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {links.map((link, index) => (
                  <div key={index} className="flex space-x-2 items-end">
                    <div className="flex-1">
                      <Label htmlFor={`url-${index}`}>Ссылка на видео</Label>
                      <Input
                        id={`url-${index}`}
                        value={link.url}
                        onChange={(e) => updateLink(index, 'url', e.target.value)}
                        placeholder="https://..."
                        required
                      />
                    </div>
                    <div className="w-32">
                      <Label htmlFor={`views-${index}`}>Просмотры</Label>
                      <Input
                        id={`views-${index}`}
                        type="number"
                        value={link.views}
                        onChange={(e) => updateLink(index, 'views', e.target.value)}
                        required
                      />
                    </div>
                    {links.length > 1 && (
                      <Button 
                        type="button" 
                        variant="outline" 
                        size="sm"
                        onClick={() => removeLink(index)}
                      >
                        ✕
                      </Button>
                    )}
                  </div>
                ))}
                
                <Button type="button" variant="outline" onClick={addLink}>
                  + Добавить ссылку
                </Button>
              </div>

              <div className="mt-6">
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Отправка...' : 'Подать отчет'}
                </Button>
              </div>
            </form>

            {message && (
              <Alert className="mt-4">
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Admin Page
const AdminPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [applications, setApplications] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [reports, setReports] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('applications');

  useEffect(() => {
    if (isAuthenticated && !isLoading && user?.admin_level >= 1) {
      fetchAdminData();
    }
  }, [isAuthenticated, isLoading, user]);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [appsRes, purchasesRes, reportsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/applications`),
        axios.get(`${API}/admin/purchases`),
        axios.get(`${API}/admin/reports`),
        axios.get(`${API}/admin/users`)
      ]);
      
      setApplications(appsRes.data || []);
      setPurchases(purchasesRes.data || []);
      setReports(reportsRes.data || []);
      setUsers(usersRes.data || []);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    }
    setLoading(false);
  };

  const handleApplicationAction = async (appId, action, mediaType = 0) => {
    try {
      if (action === 'approve') {
        await axios.post(`${API}/admin/applications/${appId}/approve?media_type=${mediaType}`);
      } else {
        await axios.post(`${API}/admin/applications/${appId}/reject`);
      }
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  const handlePurchaseAction = async (purchaseId, action) => {
    try {
      if (action === 'approve') {
        await axios.post(`${API}/admin/purchases/${purchaseId}/approve`);
      } else {
        await axios.post(`${API}/admin/purchases/${purchaseId}/reject`);
      }
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  const handleReportApprove = async (reportId, comment = '') => {
    try {
      await axios.post(`${API}/admin/reports/${reportId}/approve?comment=${comment}`);
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  const handleUserAction = async (userId, action, amount = 0) => {
    try {
      if (action === 'balance') {
        await axios.post(`${API}/admin/users/${userId}/balance?amount=${amount}`);
      } else if (action === 'warning') {
        await axios.post(`${API}/admin/users/${userId}/warning`);
      }
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated || user?.admin_level < 1) {
    return <Navigate to="/" />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка админ панели...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Админ панель</h1>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="applications">Заявки ({applications.filter(app => app.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="purchases">Покупки ({purchases.filter(p => p.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="reports">Отчеты ({reports.filter(r => r.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="users">Пользователи ({users.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="applications" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Заявки на регистрацию</CardTitle>
              </CardHeader>
              <CardContent>
                {applications.filter(app => app.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых заявок</div>
                ) : (
                  applications.filter(app => app.status === 'pending').map((app) => (
                    <div key={app.id} className="border rounded-lg p-4 mb-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h3 className="font-semibold">{app.data.nickname}</h3>
                          <p><strong>Логин:</strong> {app.data.login}</p>
                          <p><strong>VK:</strong> <a href={app.data.vk_link} target="_blank" rel="noopener noreferrer" className="text-blue-600">Ссылка</a></p>
                          <p><strong>Канал:</strong> <a href={app.data.channel_link} target="_blank" rel="noopener noreferrer" className="text-blue-600">Ссылка</a></p>
                        </div>
                        <div className="flex flex-col space-y-2">
                          <div className="flex space-x-2">
                            <Button onClick={() => handleApplicationAction(app.id, 'approve', 0)}>
                              Одобрить (Бесплатное)
                            </Button>
                            <Button onClick={() => handleApplicationAction(app.id, 'approve', 1)}>
                              Одобрить (Платное)
                            </Button>
                          </div>
                          <Button variant="destructive" onClick={() => handleApplicationAction(app.id, 'reject')}>
                            Отклонить
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="purchases" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Заявки на покупки</CardTitle>
              </CardHeader>
              <CardContent>
                {purchases.filter(purchase => purchase.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых заявок на покупки</div>
                ) : (
                  purchases.filter(purchase => purchase.status === 'pending').map((purchase) => (
                    <div key={purchase.id} className="border rounded-lg p-4 mb-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold">{purchase.user_nickname}</h3>
                          <p><strong>Товар:</strong> {purchase.item_name}</p>
                          <p><strong>Количество:</strong> {purchase.quantity}</p>
                          <p><strong>Цена:</strong> {purchase.total_price} MC</p>
                        </div>
                        <div className="flex space-x-2">
                          <Button onClick={() => handlePurchaseAction(purchase.id, 'approve')}>
                            Одобрить
                          </Button>
                          <Button variant="destructive" onClick={() => handlePurchaseAction(purchase.id, 'reject')}>
                            Отклонить
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Отчеты на рассмотрении</CardTitle>
              </CardHeader>
              <CardContent>
                {reports.filter(report => report.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых отчетов</div>
                ) : (
                  reports.filter(report => report.status === 'pending').map((report) => (
                    <div key={report.id} className="border rounded-lg p-4 mb-4">
                      <div className="mb-4">
                        <h3 className="font-semibold">{report.user_nickname}</h3>
                        <div className="space-y-1 mt-2">
                          {report.links.map((link, index) => (
                            <div key={index} className="flex justify-between">
                              <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                {link.url}
                              </a>
                              <span>{link.views} просмотров</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Input placeholder="Комментарий..." id={`comment-${report.id}`} className="flex-1" />
                        <Button onClick={() => {
                          const comment = document.getElementById(`comment-${report.id}`).value;
                          handleReportApprove(report.id, comment);
                        }}>
                          Одобрить
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Управление пользователями</CardTitle>
              </CardHeader>
              <CardContent>
                {users.map((userItem) => (
                  <div key={userItem.id} className="border rounded-lg p-4 mb-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <h3 className="font-semibold">{userItem.nickname}</h3>
                        <p><strong>Логин:</strong> {userItem.login}</p>
                        <p><strong>Баланс:</strong> {userItem.balance} MC</p>
                        <p><strong>Предупреждения:</strong> {userItem.warnings || 0}/3</p>
                      </div>
                      <div>
                        <p><strong>Статус:</strong> {userItem.is_approved ? 'Одобрен' : 'Не одобрен'}</p>
                        <p><strong>Тип:</strong> {userItem.media_type === 1 ? 'Платное' : 'Бесплатное'}</p>
                        <p><strong>Админ:</strong> {userItem.admin_level > 0 ? 'Да' : 'Нет'}</p>
                      </div>
                      <div className="space-y-2">
                        <div className="flex space-x-2">
                          <Input placeholder="Сумма" id={`balance-${userItem.id}`} type="number" className="w-20" />
                          <Button size="sm" onClick={() => {
                            const amount = document.getElementById(`balance-${userItem.id}`).value;
                            if (amount) handleUserAction(userItem.id, 'balance', parseInt(amount));
                          }}>
                            +/- MC
                          </Button>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleUserAction(userItem.id, 'warning')}
                          className="w-full"
                          disabled={userItem.warnings >= 3}
                        >
                          Выдать предупреждение
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/media-list" element={<MediaListPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/shop" element={<ShopPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;