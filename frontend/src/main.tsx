import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Routes,Route,Navigate} from 'react-router-dom';
import {BuyerLayout,SellerLayout} from './layouts';
import {ActivityPage,Audit,BuyerOrders,BuyerOverview,Cart,ChooseRole,Compare,Confirm,Docs,Flow,Landing,OrderSuccess,Payment,SellerDirectory,SellerFeedback,SellerOrders,SellerOverview,SellerProducts,SellerReport,SellerRequests,Shop,Tools} from './pages';
import './style.css';
import './app.css';
import './payment.css';

function App(){return <BrowserRouter><Routes>
  <Route path="/" element={<Landing/>}/><Route path="/choose-role" element={<ChooseRole/>}/>
  <Route path="/buyer" element={<BuyerLayout/>}><Route index element={<BuyerOverview/>}/><Route path="shop" element={<Shop/>}/><Route path="compare" element={<Compare/>}/><Route path="cart" element={<Cart/>}/><Route path="confirm" element={<Confirm/>}/><Route path="payment" element={<Payment/>}/><Route path="orders" element={<BuyerOrders/>}/><Route path="orders/:id" element={<OrderSuccess/>}/><Route path="activity" element={<ActivityPage/>}/></Route>
  <Route path="/seller" element={<SellerDirectory/>}/><Route path="/seller/:id" element={<SellerLayout/>}><Route index element={<SellerOverview/>}/><Route path="products" element={<SellerProducts/>}/><Route path="requests" element={<SellerRequests/>}/><Route path="feedback" element={<SellerFeedback/>}/><Route path="orders" element={<SellerOrders/>}/><Route path="report" element={<SellerReport/>}/></Route>
  <Route path="/audit" element={<Audit/>}/><Route path="/tools" element={<Tools/>}/><Route path="/flow" element={<Flow/>}/><Route path="/docs" element={<Docs/>}/><Route path="*" element={<Navigate to="/"/>}/>
</Routes></BrowserRouter>}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
